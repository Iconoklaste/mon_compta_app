# controllers/api_v1.py
"""API v1 de Loova : le branchement des agents du studio.

Sert à créer et renseigner des projets depuis l'extérieur (clients, projets,
phases, jalons, équipe, notes de réunion). Ni comptabilité, ni facturation, ni
suppression : ce qui se supprime se supprime dans Loova, à la main.

Activation, dans le .env du serveur (jamais dans le code, le dépôt est public) :

    LOOVA_API_TOKEN=<jeton de 32 caractères au moins>
    LOOVA_API_USER=<e-mail du compte Loova au nom duquel l'API agit>

Tant que l'une des deux lignes manque, toutes les routes répondent 404.
Chaque appel présente le jeton dans l'en-tête `Authorization: Bearer <jeton>`
(ou `X-Loova-Token: <jeton>`). L'API ne voit et ne touche que l'organisation
du compte LOOVA_API_USER ; les projets créés lui appartiennent.

Les erreurs sont en JSON : {"erreur": "..."}.
"""
import hmac
import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, g, jsonify, request, url_for
from werkzeug.exceptions import HTTPException

from controllers.db_manager import db
from models import Client, EquipeMembre, Jalon, NoteReunion, Phase, Projet, User
from utils.ecritures_comptable_util import creer_compte_pour_client
from utils.nettoyage_html import nettoyer_html, texte_seul

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

LONGUEUR_MIN_JETON = 32
STATUTS_PROJET = ('En attente', 'En cours', 'Terminé', 'Annulé')
STATUTS_PHASE = ('En attente', 'En cours', 'Terminée')
FORME_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
FORME_CODE_POSTAL = re.compile(r'^\d{5}$')


class ErreurApi(Exception):
    """Erreur renvoyée telle quelle à l'appelant."""

    def __init__(self, message, code=400, **complement):
        super().__init__(message)
        self.message = message
        self.code = code
        self.complement = complement


def _reponse_erreur(message, code, **complement):
    return jsonify({'erreur': message, **complement}), code


# --- Accès -------------------------------------------------------------------

def _jeton_presente():
    entete = request.headers.get('Authorization', '')
    if entete.startswith('Bearer '):
        return entete[len('Bearer '):].strip()
    return request.headers.get('X-Loova-Token', '').strip()


@api_v1_bp.before_request
def _controler_l_acces():
    attendu = current_app.config.get('LOOVA_API_TOKEN') or ''
    mail = current_app.config.get('LOOVA_API_USER') or ''
    if len(attendu) < LONGUEUR_MIN_JETON or not mail:
        return _reponse_erreur("Introuvable.", 404)

    presente = _jeton_presente()
    if not presente or not hmac.compare_digest(presente.encode('utf-8'), attendu.encode('utf-8')):
        return _reponse_erreur("Jeton absent ou invalide.", 401)

    utilisateur = User.query.filter_by(mail=mail).first()
    if utilisateur is None:
        current_app.logger.error("API v1 : LOOVA_API_USER ne correspond à aucun compte.")
        return _reponse_erreur("LOOVA_API_USER ne correspond à aucun compte Loova.", 503)
    g.api_user = utilisateur


@api_v1_bp.after_request
def _journaliser(reponse):
    if request.method != 'GET':
        current_app.logger.info("API v1 : %s %s -> %s", request.method, request.path, reponse.status_code)
    return reponse


@api_v1_bp.errorhandler(ErreurApi)
def _sur_erreur_api(erreur):
    db.session.rollback()
    return _reponse_erreur(erreur.message, erreur.code, **erreur.complement)


@api_v1_bp.errorhandler(HTTPException)
def _sur_erreur_http(erreur):
    return _reponse_erreur(erreur.description, erreur.code)


@api_v1_bp.errorhandler(Exception)
def _sur_erreur_inattendue(erreur):
    db.session.rollback()
    current_app.logger.exception("API v1 : erreur inattendue sur %s %s", request.method, request.path)
    return _reponse_erreur("Erreur interne. Le détail est dans le journal du serveur.", 500)


# --- Lecture du corps de la requête ------------------------------------------

class _Corps:
    """Corps JSON d'une requête : refuse les champs inconnus, convertit les valeurs.

    Un champ absent n'est pas touché. Un champ présent et vide (null ou "")
    efface la valeur, sauf s'il est obligatoire.
    """

    def __init__(self, admis, obligatoires=()):
        donnees = request.get_json(silent=True)
        if not isinstance(donnees, dict):
            raise ErreurApi("Le corps de la requête doit être un objet JSON.")
        inconnus = sorted(set(donnees) - set(admis))
        if inconnus:
            raise ErreurApi("Champ(s) inconnu(s) : %s. Champs admis : %s."
                            % (', '.join(inconnus), ', '.join(admis)))
        manquants = [c for c in obligatoires if donnees.get(c) in (None, '')]
        if manquants:
            raise ErreurApi("Champ(s) obligatoire(s) manquant(s) : %s." % ', '.join(manquants))
        self.donnees = donnees

    def __contains__(self, champ):
        return champ in self.donnees

    def brut(self, champ):
        return self.donnees.get(champ)

    def texte(self, champ, longueur_max):
        valeur = self.donnees.get(champ)
        if valeur is None:
            return None
        if not isinstance(valeur, str):
            raise ErreurApi("« %s » doit être un texte." % champ)
        valeur = valeur.strip()
        if len(valeur) > longueur_max:
            raise ErreurApi("« %s » dépasse %d caractères." % (champ, longueur_max))
        return valeur or None

    def texte_requis(self, champ, longueur_max):
        valeur = self.texte(champ, longueur_max)
        if valeur is None:
            raise ErreurApi("« %s » ne peut pas être vide." % champ)
        return valeur

    def date(self, champ):
        valeur = self.donnees.get(champ)
        if valeur in (None, ''):
            return None
        try:
            return date.fromisoformat(valeur)
        except (TypeError, ValueError):
            raise ErreurApi("« %s » doit être une date au format AAAA-MM-JJ." % champ)

    def date_requise(self, champ):
        valeur = self.date(champ)
        if valeur is None:
            raise ErreurApi("« %s » ne peut pas être vide." % champ)
        return valeur

    def choix(self, champ, valeurs):
        valeur = self.donnees.get(champ)
        if valeur not in valeurs:
            raise ErreurApi("« %s » doit valoir : %s." % (champ, ' | '.join(valeurs)))
        return valeur

    def montant(self, champ):
        valeur = self.donnees.get(champ)
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float, str)):
            raise ErreurApi("« %s » doit être un nombre." % champ)
        try:
            montant = Decimal(str(valeur)).quantize(Decimal('0.01'))
        except InvalidOperation:
            raise ErreurApi("« %s » doit être un nombre." % champ)
        if not Decimal('0') <= montant < Decimal('100000000'):
            raise ErreurApi("« %s » doit être compris entre 0 et 99 999 999,99." % champ)
        return montant

    def booleen(self, champ):
        valeur = self.donnees.get(champ)
        if not isinstance(valeur, bool):
            raise ErreurApi("« %s » doit valoir true ou false." % champ)
        return valeur

    def entier(self, champ):
        valeur = self.donnees.get(champ)
        if isinstance(valeur, bool) or not isinstance(valeur, int):
            raise ErreurApi("« %s » doit être un entier." % champ)
        return valeur


def _controler_l_ordre(debut, fin):
    if debut and fin and fin < debut:
        raise ErreurApi("La date de fin ne peut pas précéder la date de début.")


# --- Recherche des objets, toujours dans l'organisation du compte ------------

def _organisation_id():
    return g.api_user.organisation_id


def _projet(projet_id):
    projet = Projet.query.filter_by(id=projet_id, organisation_id=_organisation_id()).first()
    if projet is None:
        raise ErreurApi("Projet %d introuvable." % projet_id, 404)
    return projet


def _du_projet(modele, objet_id, libelle):
    """Phase, jalon, membre ou note, si son projet est dans l'organisation."""
    objet = db.session.get(modele, objet_id)
    if objet is None or objet.projet.organisation_id != _organisation_id():
        raise ErreurApi("%s %d introuvable." % (libelle, objet_id), 404)
    return objet


def _client(client_id):
    client = Client.query.filter_by(id=client_id, organisation_id=_organisation_id()).first()
    if client is None:
        raise ErreurApi("Client %d introuvable." % client_id, 404)
    return client


# --- Mise en forme des réponses ----------------------------------------------

def _iso(valeur):
    return valeur.isoformat() if valeur else None


def _client_json(client):
    return {
        'id': client.id, 'nom': client.nom, 'adresse': client.adresse,
        'code_postal': client.code_postal, 'ville': client.ville,
        'telephone': client.telephone, 'mail': client.mail,
    }


def _jalon_json(jalon):
    return {'id': jalon.id, 'nom': jalon.nom, 'date': _iso(jalon.date),
            'atteint': bool(jalon.atteint), 'phase_id': jalon.phase_id}


def _phase_json(phase):
    return {
        'id': phase.id, 'nom': phase.nom, 'statut': phase.statut,
        'date_debut': _iso(phase.date_debut), 'date_fin': _iso(phase.date_fin),
        'avancement': phase.progress or 0,
        'jalons': [_jalon_json(j) for j in sorted(phase.jalons, key=lambda j: (j.date, j.id))],
    }


def _membre_json(membre):
    return {'id': membre.id, 'nom': membre.nom, 'email': membre.email,
            'role_projet': membre.role_projet, 'compte_loova': membre.user_id is not None}


def _note_json(note):
    return {'id': note.id, 'date': _iso(note.date.date()) if note.date else None,
            'contenu': note.contenu, 'modifiee_le': _iso(note.updated_at)}


def _projet_json(projet, complet=False):
    resultat = {
        'id': projet.id, 'reference': projet.reference, 'nom': projet.nom,
        'statut': projet.statut,
        'date_debut': _iso(projet.date_debut), 'date_fin': _iso(projet.date_fin),
        'prix_total': float(projet.prix_total or 0),
        'client': {'id': projet.client.id, 'nom': projet.client.nom} if projet.client else None,
        'url': url_for('projets.projet_detail', projet_id=projet.id, _external=True),
    }
    if complet:
        phases = sorted(projet.phases, key=lambda p: (p.date_debut or date.max, p.id))
        resultat['phases'] = [_phase_json(p) for p in phases]
        resultat['equipe'] = [_membre_json(m) for m in projet.membres]
        resultat['notes'] = [_note_json(n) for n in projet.notes_reunion.order_by(NoteReunion.date.desc())]
    return resultat


def _recalculer_l_avancement(phase):
    """Même règle que la page du projet : part des jalons atteints."""
    total = len(phase.jalons)
    atteints = sum(1 for j in phase.jalons if j.atteint)
    phase.progress = round(atteints / total * 100) if total else 0


# --- État --------------------------------------------------------------------

@api_v1_bp.route('/', methods=['GET'])
def etat():
    return jsonify({
        'service': 'loova', 'api': 1,
        'compte': g.api_user.nom_complet,
        'organisation': g.api_user.organisation.designation,
    })


# --- Clients -----------------------------------------------------------------

@api_v1_bp.route('/clients', methods=['GET'])
def lister_clients():
    requete = Client.query.filter_by(organisation_id=_organisation_id())
    recherche = request.args.get('q', '').strip()
    if recherche:
        requete = requete.filter(Client.nom.ilike('%' + recherche + '%'))
    return jsonify({'clients': [_client_json(c) for c in requete.order_by(Client.nom).all()]})


@api_v1_bp.route('/clients', methods=['POST'])
def creer_client():
    corps = _Corps(('nom', 'adresse', 'code_postal', 'ville', 'telephone', 'mail'), obligatoires=('nom',))
    nom = corps.texte_requis('nom', 100)
    homonyme = Client.query.filter(Client.organisation_id == _organisation_id(),
                                   db.func.lower(Client.nom) == nom.lower()).first()
    if homonyme:
        raise ErreurApi("Un client porte déjà ce nom.", 409, client=_client_json(homonyme))

    code_postal = corps.texte('code_postal', 5)
    if code_postal and not FORME_CODE_POSTAL.match(code_postal):
        raise ErreurApi("« code_postal » doit contenir 5 chiffres.")
    mail = corps.texte('mail', 100)
    if mail and not FORME_EMAIL.match(mail):
        raise ErreurApi("« mail » n'est pas une adresse e-mail.")

    client = Client(nom=nom, adresse=corps.texte('adresse', 200), code_postal=code_postal,
                    ville=corps.texte('ville', 100), telephone=corps.texte('telephone', 20),
                    mail=mail, organisation_id=_organisation_id())
    db.session.add(client)
    db.session.flush()
    # Comme dans Loova : tout client a son compte comptable 411.
    compte = creer_compte_pour_client(client, db.session)
    if not compte:
        raise ErreurApi("Le compte comptable du client n'a pas pu être créé.", 500)
    client.compte_comptable = compte
    db.session.commit()
    return jsonify({'client': _client_json(client)}), 201


# --- Projets -----------------------------------------------------------------

CHAMPS_PROJET = ('nom', 'reference', 'client_id', 'date_debut', 'date_fin', 'statut', 'prix_total')


@api_v1_bp.route('/projets', methods=['GET'])
def lister_projets():
    requete = Projet.query.filter_by(organisation_id=_organisation_id())
    reference = request.args.get('reference', '').strip()
    recherche = request.args.get('q', '').strip()
    if reference:
        requete = requete.filter(Projet.reference == reference)
    if recherche:
        motif = '%' + recherche + '%'
        requete = requete.filter(db.or_(Projet.nom.ilike(motif), Projet.reference.ilike(motif)))
    projets = requete.order_by(Projet.reference.desc(), Projet.id.desc()).all()
    return jsonify({'projets': [_projet_json(p) for p in projets]})


def _appliquer_au_projet(projet, corps):
    """Reporte sur le projet les champs présents dans le corps."""
    if 'nom' in corps:
        projet.nom = corps.texte_requis('nom', 100)
    if 'reference' in corps:
        reference = corps.texte('reference', 50)
        deja = Projet.portant_la_reference(_organisation_id(), reference, sauf_id=projet.id)
        if deja:
            raise ErreurApi("La référence « %s » est déjà portée par un autre projet." % reference,
                            409, projet=_projet_json(deja))
        projet.reference = reference
    if 'client_id' in corps:
        projet.client_id = None if corps.brut('client_id') is None else _client(corps.entier('client_id')).id
    if 'date_debut' in corps:
        projet.date_debut = corps.date('date_debut')
    if 'date_fin' in corps:
        projet.date_fin = corps.date('date_fin')
    _controler_l_ordre(projet.date_debut, projet.date_fin)
    if 'statut' in corps:
        projet.statut = corps.choix('statut', STATUTS_PROJET)
    if 'prix_total' in corps:
        projet.prix_total = corps.montant('prix_total')


@api_v1_bp.route('/projets', methods=['POST'])
def creer_projet():
    corps = _Corps(CHAMPS_PROJET, obligatoires=('nom',))
    projet = Projet(statut='En attente', prix_total=Decimal('0'),
                    organisation_id=_organisation_id(), user_id=g.api_user.id)
    # no_autoflush : les recherches de doublon ne doivent pas écrire un projet incomplet.
    with db.session.no_autoflush:
        _appliquer_au_projet(projet, corps)
    db.session.add(projet)
    db.session.commit()
    return jsonify({'projet': _projet_json(projet, complet=True)}), 201


@api_v1_bp.route('/projets/<int:projet_id>', methods=['GET'])
def lire_projet(projet_id):
    return jsonify({'projet': _projet_json(_projet(projet_id), complet=True)})


@api_v1_bp.route('/projets/<int:projet_id>', methods=['PATCH'])
def modifier_projet(projet_id):
    projet = _projet(projet_id)
    with db.session.no_autoflush:
        _appliquer_au_projet(projet, _Corps(CHAMPS_PROJET))
    db.session.commit()
    return jsonify({'projet': _projet_json(projet, complet=True)})


# --- Phases et jalons --------------------------------------------------------

def _controler_le_jalon(phase, jour):
    """Comme le formulaire de Loova : un jalon tombe dans les dates de sa phase."""
    if phase.date_debut and jour < phase.date_debut or phase.date_fin and jour > phase.date_fin:
        raise ErreurApi("Le jalon du %s tombe hors de la phase « %s » (%s → %s)."
                        % (jour.isoformat(), phase.nom, _iso(phase.date_debut) or '…', _iso(phase.date_fin) or '…'))


def _controler_les_jalons(phase):
    for jalon in phase.jalons:
        _controler_le_jalon(phase, jalon.date)


@api_v1_bp.route('/projets/<int:projet_id>/phases', methods=['POST'])
def creer_phase(projet_id):
    projet = _projet(projet_id)
    corps = _Corps(('nom', 'date_debut', 'date_fin', 'statut', 'jalons'), obligatoires=('nom',))
    phase = Phase(nom=corps.texte_requis('nom', 255), date_debut=corps.date('date_debut'),
                  date_fin=corps.date('date_fin'),
                  statut=corps.choix('statut', STATUTS_PHASE) if 'statut' in corps else 'En attente',
                  projet_id=projet.id, progress=0)
    _controler_l_ordre(phase.date_debut, phase.date_fin)

    jalons = corps.brut('jalons') or []
    if not isinstance(jalons, list) or not all(isinstance(j, dict) for j in jalons):
        raise ErreurApi("« jalons » doit être une liste d'objets {nom, date, atteint}.")
    for numero, donnees in enumerate(jalons, start=1):
        inconnus = sorted(set(donnees) - {'nom', 'date', 'atteint'})
        nom = donnees.get('nom')
        atteint = donnees.get('atteint', False)
        if inconnus or not isinstance(nom, str) or not nom.strip() or len(nom.strip()) > 255 \
                or not isinstance(atteint, bool):
            raise ErreurApi("Jalon n° %d : attendu {nom, date, atteint}, nom de 255 caractères au plus." % numero)
        try:
            jour = date.fromisoformat(donnees.get('date'))
        except (TypeError, ValueError):
            raise ErreurApi("Jalon n° %d : « date » doit être au format AAAA-MM-JJ." % numero)
        _controler_le_jalon(phase, jour)
        phase.jalons.append(Jalon(nom=nom.strip(), date=jour, atteint=atteint, projet_id=projet.id))

    _recalculer_l_avancement(phase)
    db.session.add(phase)
    db.session.commit()
    return jsonify({'phase': _phase_json(phase)}), 201


@api_v1_bp.route('/phases/<int:phase_id>', methods=['PATCH'])
def modifier_phase(phase_id):
    phase = _du_projet(Phase, phase_id, "Phase")
    corps = _Corps(('nom', 'date_debut', 'date_fin', 'statut'))
    if 'nom' in corps:
        phase.nom = corps.texte_requis('nom', 255)
    if 'date_debut' in corps:
        phase.date_debut = corps.date('date_debut')
    if 'date_fin' in corps:
        phase.date_fin = corps.date('date_fin')
    _controler_l_ordre(phase.date_debut, phase.date_fin)
    _controler_les_jalons(phase)
    if 'statut' in corps:
        phase.statut = corps.choix('statut', STATUTS_PHASE)
    db.session.commit()
    return jsonify({'phase': _phase_json(phase)})


@api_v1_bp.route('/phases/<int:phase_id>/jalons', methods=['POST'])
def creer_jalon(phase_id):
    phase = _du_projet(Phase, phase_id, "Phase")
    corps = _Corps(('nom', 'date', 'atteint'), obligatoires=('nom', 'date'))
    jalon = Jalon(nom=corps.texte_requis('nom', 255), date=corps.date_requise('date'),
                  atteint=corps.booleen('atteint') if 'atteint' in corps else False,
                  projet_id=phase.projet_id)
    _controler_le_jalon(phase, jalon.date)
    phase.jalons.append(jalon)
    _recalculer_l_avancement(phase)
    db.session.commit()
    return jsonify({'jalon': _jalon_json(jalon), 'phase': _phase_json(phase)}), 201


@api_v1_bp.route('/jalons/<int:jalon_id>', methods=['PATCH'])
def modifier_jalon(jalon_id):
    jalon = _du_projet(Jalon, jalon_id, "Jalon")
    corps = _Corps(('nom', 'date', 'atteint'))
    if 'nom' in corps:
        jalon.nom = corps.texte_requis('nom', 255)
    if 'date' in corps:
        jalon.date = corps.date_requise('date')
        _controler_le_jalon(jalon.phase, jalon.date)
    if 'atteint' in corps:
        jalon.atteint = corps.booleen('atteint')
    _recalculer_l_avancement(jalon.phase)
    db.session.commit()
    return jsonify({'jalon': _jalon_json(jalon), 'phase': _phase_json(jalon.phase)})


# --- Équipe ------------------------------------------------------------------

def _appliquer_au_membre(membre, corps):
    if 'nom' in corps:
        membre.nom = corps.texte_requis('nom', 100)
    if 'role_projet' in corps:
        membre.role_projet = corps.texte('role_projet', 80)
    if 'email' in corps:
        email = corps.texte_requis('email', 120)
        if not FORME_EMAIL.match(email):
            raise ErreurApi("« email » n'est pas une adresse e-mail.")
        doublon = EquipeMembre.query.filter(EquipeMembre.projet_id == membre.projet_id,
                                            db.func.lower(EquipeMembre.email) == email.lower(),
                                            EquipeMembre.id != membre.id).first()
        if doublon:
            raise ErreurApi("%s (%s) fait déjà partie de l'équipe." % (doublon.nom, doublon.email),
                            409, membre=_membre_json(doublon))
        membre.email = email
        # Rattache le membre à son compte Loova s'il en a un dans l'organisation.
        compte = User.query.filter(User.organisation_id == _organisation_id(),
                                   db.func.lower(User.mail) == email.lower()).first()
        membre.user_id = compte.id if compte else None


@api_v1_bp.route('/projets/<int:projet_id>/equipe', methods=['POST'])
def ajouter_membre(projet_id):
    projet = _projet(projet_id)
    corps = _Corps(('nom', 'email', 'role_projet'), obligatoires=('nom', 'email'))
    membre = EquipeMembre(projet_id=projet.id)
    with db.session.no_autoflush:
        _appliquer_au_membre(membre, corps)
    db.session.add(membre)
    db.session.commit()
    return jsonify({'membre': _membre_json(membre)}), 201


@api_v1_bp.route('/equipe/<int:membre_id>', methods=['PATCH'])
def modifier_membre(membre_id):
    membre = _du_projet(EquipeMembre, membre_id, "Membre")
    with db.session.no_autoflush:
        _appliquer_au_membre(membre, _Corps(('nom', 'email', 'role_projet')))
    db.session.commit()
    return jsonify({'membre': _membre_json(membre)})


# --- Notes de réunion --------------------------------------------------------

def _appliquer_a_la_note(note, corps):
    if 'date' in corps:
        note.date = datetime.combine(corps.date_requise('date'), time.min)
    if 'contenu' in corps:
        contenu = corps.brut('contenu')
        if not isinstance(contenu, str):
            raise ErreurApi("« contenu » doit être un texte (HTML simple).")
        # La page du projet affiche ce HTML tel quel : on n'en garde que la mise en forme.
        contenu = nettoyer_html(contenu)
        if not texte_seul(contenu):
            raise ErreurApi("« contenu » est vide.")
        note.contenu = contenu


@api_v1_bp.route('/projets/<int:projet_id>/notes', methods=['POST'])
def ajouter_note(projet_id):
    projet = _projet(projet_id)
    note = NoteReunion(projet_id=projet.id)
    _appliquer_a_la_note(note, _Corps(('date', 'contenu'), obligatoires=('date', 'contenu')))
    db.session.add(note)
    db.session.commit()
    return jsonify({'note': _note_json(note)}), 201


@api_v1_bp.route('/notes/<int:note_id>', methods=['PATCH'])
def modifier_note(note_id):
    note = _du_projet(NoteReunion, note_id, "Note")
    _appliquer_a_la_note(note, _Corps(('date', 'contenu')))
    db.session.commit()
    return jsonify({'note': _note_json(note)})
