# c:\wamp\www\mon_compta_app\controllers\clients_controller.py

from flask import Blueprint, request, jsonify, render_template, flash, session, redirect, url_for
from flask_wtf.csrf import validate_csrf, CSRFError
from sqlalchemy.exc import IntegrityError, DataError, SQLAlchemyError
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client, Projet, Transaction, User, Organisation
from forms.forms import ClientForm
from utils.ecritures_comptable_util import creer_compte_pour_client
import itertools
import json
import logging

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')
logger = logging.getLogger(__name__)

@clients_bp.route('/')
@login_required
def clients():
    """Render the clients list page."""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        flash("Impossible de déterminer votre organisation.", "danger")
        return redirect(url_for('users.index'))

    clients = Client.query.filter_by(organisation_id=user.organisation_id).order_by(Client.nom).all()
    return render_template('clients.html',
                           clients=clients,
                           current_page='CRM')

# --- Route pour AFFICHER et TRAITER le formulaire standard d'ajout ---
@clients_bp.route('/ajouter', methods=['GET', 'POST']) # Accepte GET et POST
@login_required
def ajouter_client_page():
    """Affiche le formulaire (GET) ou traite l'ajout depuis la page dédiée (POST)."""
    form = ClientForm() # Instancier le formulaire

    # --- Traitement de la soumission POST (formulaire standard) ---
    if form.validate_on_submit(): # Gère la validation ET le CSRF pour les formulaires standard
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user or not user.organisation_id:
            flash("Impossible de déterminer votre organisation.", "danger")
            # Renvoyer vers le formulaire avec les données saisies
            return render_template('ajouter_client_page.html', form=form, current_page='CRM')

        organisation_id = user.organisation_id

        try:
            # Création de l'objet Client
            new_client = Client(
                nom=form.nom.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail=form.mail.data,
                organisation_id=organisation_id
            )
            db.session.add(new_client)
            db.session.flush() # Obtenir l'ID pour la création du compte
            logger.info(f"Client '{new_client.nom}' (Formulaire standard pré-commit ID: {new_client.id}) ajouté à la session.")

            # Création du compte comptable
            compte_cree = creer_compte_pour_client(new_client, db.session)
            if not compte_cree:
                db.session.rollback()
                flash("Erreur lors de la création du compte comptable associé.", 'danger')
                return render_template('ajouter_client_page.html', form=form, current_page='CRM')

            new_client.compte_comptable = compte_cree
            db.session.commit()
            logger.info(f"Client ID {new_client.id} (Formulaire standard) commité avec succès.")
            flash('Client ajouté avec succès!', 'success')
            return redirect(url_for('clients.clients')) # Rediriger vers la liste

        except IntegrityError as e:
            db.session.rollback()
            logger.warning(f"Erreur d'intégrité lors de l'ajout du client (formulaire standard): {e}")
            error_msg = 'Erreur de base de données (doublon?).'
            if 'client.mail' in str(e.orig).lower() or 'unique constraint failed: client.mail' in str(e.orig).lower():
                 error_msg = "Cet email est déjà utilisé par un autre client."
                 form.mail.errors.append(error_msg) # Ajouter l'erreur au champ
            flash(error_msg, 'danger')
            # Renvoyer le formulaire avec l'erreur

        except (DataError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Erreur DB lors de l'ajout du client (formulaire standard): {e}", exc_info=True)
            flash(f"Erreur de base de données: {e}", 'danger')
            # Renvoyer le formulaire

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur inattendue lors de l'ajout du client (formulaire standard): {e}", exc_info=True)
            flash(f"Une erreur inattendue est survenue: {e}", 'danger')
            # Renvoyer le formulaire

    # --- Affichage du formulaire (requête GET ou si validation POST échoue) ---
    # Si c'est une requête GET, ou si form.validate_on_submit() a échoué, on affiche la page.
    # Les erreurs de validation sont automatiquement gérées par WTForms et affichées dans le template.
    if request.method == 'POST' and not form.errors:
         # Si c'était un POST mais pas une erreur gérée explicitement au-dessus (ex: IntegrityError),
         # on peut flasher un message générique si besoin, mais WTForms devrait avoir mis les erreurs.
         flash("Erreur de validation. Veuillez vérifier les champs.", 'warning')

    return render_template('ajouter_client_page.html',
                           form=form, # Passer le formulaire (peut contenir des erreurs)
                           current_page='CRM')


# --- Route POST distincte pour traiter l'ajout via AJAX ---
@clients_bp.route('/ajouter/ajax', methods=['POST']) # Nouvelle URL spécifique AJAX
@login_required
def ajouter_client_ajax():
    """Traite la soumission AJAX pour ajouter un nouveau client."""
    # Pas besoin de vérifier is_ajax ici, car cette route est dédiée AJAX

    # --- Validation CSRF (pour AJAX via Header) ---
    try:
        csrf_token_value = request.headers.get('X-CSRFToken')
        if not csrf_token_value:
             raise CSRFError("CSRF token manquant dans l'en-tête X-CSRFToken.")
        validate_csrf(csrf_token_value) # Valide le token de l'en-tête
    except CSRFError as e:
        logger.warning(f"Erreur CSRF lors de l'ajout de client (AJAX): {e}")
        message = 'Erreur de sécurité (CSRF). Veuillez rafraîchir la page et réessayer.'
        return jsonify({'success': False, 'errors': {'_csrf': message}}), 400 # Réponse JSON

    # --- Récupération et validation des données JSON ---
    form_data = request.get_json()
    if not form_data:
        return jsonify({'success': False, 'errors': {'_error': "Données JSON manquantes ou invalides."}}), 400

    # Utiliser data= pour initialiser le formulaire avec le JSON
    form = ClientForm(data=form_data)

    # --- Récupérer l'organisation de l'utilisateur ---
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        message = "Impossible de déterminer votre organisation."
        return jsonify({'success': False, 'errors': {'_error': message}}), 400

    organisation_id = user.organisation_id

    if form.validate(): # Valider les données reçues
        try:
            # Création de l'objet Client
            new_client = Client(
                nom=form.nom.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail=form.mail.data,
                organisation_id=organisation_id
            )
            db.session.add(new_client)
            db.session.flush()
            logger.info(f"Client '{new_client.nom}' (AJAX pré-commit ID: {new_client.id}) ajouté à la session.")

            # Création du compte comptable
            compte_cree = creer_compte_pour_client(new_client, db.session)
            if not compte_cree:
                db.session.rollback()
                message = "Erreur lors de la création du compte comptable associé."
                logger.error(f"{message} pour client potentiel {new_client.nom} (AJAX)")
                return jsonify({'success': False, 'errors': {'_error': message}}), 500 # Réponse JSON

            new_client.compte_comptable = compte_cree
            db.session.commit()
            logger.info(f"Client ID {new_client.id} (AJAX) commité avec succès.")

            # --- Réponse Succès AJAX ---
            return jsonify({'success': True, 'client_id': new_client.id, 'client_nom': new_client.nom})

        except IntegrityError as e:
            db.session.rollback()
            logger.warning(f"Erreur d'intégrité lors de l'ajout du client (AJAX): {e}")
            error_msg = 'Erreur de base de données (doublon?).'
            if 'client.mail' in str(e.orig).lower() or 'unique constraint failed: client.mail' in str(e.orig).lower():
                 error_msg = "Cet email est déjà utilisé par un autre client."
                 # Ajouter l'erreur au formulaire pour la réponse JSON
                 if 'mail' not in form.errors: form.errors['mail'] = []
                 form.errors['mail'].append(error_msg)

            # Renvoyer les erreurs du formulaire ou l'erreur générique
            return jsonify({'success': False, 'errors': form.errors or {'_error': error_msg}}), 400

        except (DataError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Erreur DB lors de l'ajout du client (AJAX): {e}", exc_info=True)
            message = f"Erreur de base de données: {e}"
            return jsonify({'success': False, 'errors': {'_error': message}}), 500

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur inattendue lors de l'ajout du client (AJAX): {e}", exc_info=True)
            message = f"Une erreur inattendue est survenue: {e}"
            return jsonify({'success': False, 'errors': {'_error': message}}), 500
    else:
        # --- La validation WTForms a échoué (AJAX) ---
        logger.debug(f"Échec de validation du formulaire d'ajout client (AJAX): {form.errors}")
        return jsonify({'success': False, 'errors': form.errors}), 400 # Renvoyer les erreurs


@clients_bp.route('/<int:client_id>')
@login_required
def client_dashboard(client_id):
    """Render the client dashboard."""
    # ... (le reste de la fonction client_dashboard reste inchangé) ...
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    client = Client.query.filter_by(id=client_id, organisation_id=user.organisation_id).first_or_404()

    projets = client.projets
    transactions = list(itertools.chain.from_iterable(projet.transactions for projet in projets))

    total_paye = sum(t.montant for t in transactions if t.type == "Entrée" and t.reglement == "Réglée")
    total_facture = sum(t.montant for t in transactions if t.type == "Entrée")
    solde_du_client = total_facture - total_paye

    return render_template(
        'client_dashboard.html',
        client=client,
        projets=projets,
        transactions=transactions,
        total_paye=total_paye,
        total_facture=total_facture,
        solde_du_client=solde_du_client,
        current_page='CRM'
    )
