# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import (HiddenField, StringField, DateField,
                     widgets, SelectField, IntegerField,
                     BooleanField, SubmitField, FieldList,
                     FormField, FloatField, TextAreaField, PasswordField, EmailField,
                     TelField, FileField, DateTimeLocalField)
# Ajoute cette ligne ici
from flask_wtf.file import FileField, FileAllowed, FileRequired # Import file field components
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import (DataRequired, Email, Optional,
                                EqualTo, Regexp, ValidationError,
                                NumberRange, Length)

from models.clients import Client
from models.organisations import Organisation
from models.exercices import ExerciceComptable
from models import CompteComptable
from models.compte_comptable import ClasseCompte

from datetime import date, datetime

def coerce_int_or_none(x):
    """Tente de convertir en int, retourne None en cas d'échec ou si vide."""
    if x == '' or x is None:
        return None
    try:
        return int(x)
    except (ValueError, TypeError):
        return None


class DateInput(widgets.TextInput):
    input_type = 'date'
    validation_attrs = ['required', 'min', 'max', 'step'] # Add this line

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class ModifierProfilForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    mail = EmailField('Email', validators=[DataRequired(), Email()])
    telephone = TelField('Téléphone', validators=[Optional()])
    password = PasswordField('Nouveau mot de passe')

class AjouterUserForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    mail = EmailField('Email', validators=[DataRequired(), Email()])
    telephone = TelField('Téléphone', validators=[Optional()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), EqualTo('confirm_password', message='Les mots de passe doivent correspondre')])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired()])
    organisation = SelectField('Organisation', coerce=str, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(AjouterUserForm, self).__init__(*args, **kwargs)
        self.organisation.choices = [(org.designation, org.designation) for org in Organisation.query.all()]

class AjouterUserFormDemo(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    mail = EmailField('Email', validators=[DataRequired(), Email()])
    telephone = TelField('Téléphone', validators=[Optional()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), EqualTo('confirm_password', message='Les mots de passe doivent correspondre')])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired()])
    organisation = SelectField('Organisation', coerce=str, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(AjouterUserForm, self).__init__(*args, **kwargs)
        self.organisation.choices = [(org.designation, org.designation) for org in Organisation.query.all()]


class ProjetForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    date_debut = DateField('Date de début', validators=[DataRequired()])
    date_fin = DateField('Date de fin', validators=[DataRequired()])
    statut = SelectField('Statut', choices=[('En attente', 'En attente'), ('En cours', 'En cours'), ('Terminé', 'Terminé'), ('Annulé', 'Annulé')], validators=[DataRequired()])
    prix_total = IntegerField('Prix total', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(ProjetForm, self).__init__(*args, **kwargs)
        self.client_id.choices = [(client.id, client.nom) for client in Client.query.all()]

class JalonForm(FlaskForm):
    id = HiddenField()
    nom = StringField('Nom', validators=[DataRequired()], render_kw={'placeholder': 'Entrez le nom du jalon'})
    date = DateField('Date', validators=[DataRequired()], widget=DateInput())
    atteint = BooleanField('Atteint')
    class Meta:
        csrf = False

class PhaseForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    date_debut = DateField('Date de début', validators=[DataRequired()], default=date.today)
    date_fin = DateField('Date de fin', validators=[DataRequired()], default=date.today)
    statut = SelectField('Statut', choices=[('En cours', 'En cours'), ('Terminée', 'Terminée'), ('En attente', 'En attente')])
    jalons = FieldList(FormField(JalonForm), min_entries=1)  # Add this line
    submit = SubmitField('Enregistrer')

    # --- Validation 1: Date de fin >= Date de début ---
    def validate_date_fin(self, field):
        # Vérifie si les deux dates sont présentes avant de comparer
        if self.date_debut.data and field.data:
            if field.data < self.date_debut.data:
                # Lève une erreur de validation qui sera attachée au champ date_fin
                raise ValidationError('La date de fin ne peut pas être antérieure à la date de début.')

    # --- Validation 2: Date des jalons dans l'intervalle de la phase ---
    def validate_jalons(self, field):
        # 'field' ici est le FieldList 'jalons'
        has_error = False # Pour éviter de lever plusieurs fois la même erreur générale si besoin

        # Vérifie si les dates de la phase sont valides avant de vérifier les jalons
        # On vérifie aussi si la validation précédente (validate_date_fin) n'a pas déjà échoué
        if self.date_debut.data and self.date_fin.data and not self.date_fin.errors:
            phase_start = self.date_debut.data
            phase_end = self.date_fin.data

            # Itère sur chaque sous-formulaire (JalonForm) dans le FieldList
            for index, jalon_entry in enumerate(field.entries):
                jalon_date = jalon_entry.form.date.data

                # Vérifie si le jalon a une date définie
                if jalon_date:
                    if not (phase_start <= jalon_date <= phase_end):
                        # Ajoute une erreur spécifique au champ 'date' de ce jalon particulier
                        jalon_entry.form.date.errors.append(
                            f"La date doit être comprise entre le {phase_start.strftime('%d/%m/%Y')} et le {phase_end.strftime('%d/%m/%Y')}."
                        )
                        has_error = True # Marque qu'au moins une erreur a été trouvée
        # Optionnel: Si vous voulez une erreur générale sur la liste des jalons en plus des erreurs spécifiques
        if has_error:
           raise ValidationError("Une ou plusieurs dates de jalon sont en dehors des dates de la phase.")

class OrganisationForm(FlaskForm):
    designation = StringField('Désignation', validators=[DataRequired()])
    siret = StringField('Numéro SIRET', validators=[DataRequired(), Regexp(r'^\d{14}$', message="Le SIRET doit contenir 14 chiffres.")])
    exonere_tva = BooleanField('Exonéré de TVA')
    tva_intracommunautaire = StringField('Numéro TVA Intracommunautaire', validators=[Optional(), Regexp(r'^[A-Z]{2}[0-9A-Z]{11,13}$', message="Le numéro TVA intracommunautaire doit commencer par deux lettres majuscules suivies de 11 à 13 chiffres ou lettres.")])
    forme_juridique = SelectField('Forme Juridique', choices=[
        ('', 'Sélectionnez une forme juridique'),
        ('SARL', 'SARL'),
        ('EURL', 'EURL'),
        ('SAS', 'SAS'),
        ('SA', 'SA'),
        ('SASU', 'SASU'),
        ('Association', 'Association'),
        ('Entreprise Individuelle', 'Entreprise Individuelle'),
        ('Autre', 'Autre')
    ], validators=[DataRequired()])
    adresse = StringField('Adresse')
    code_postal = StringField('Code Postal', validators=[Optional(), Regexp(r'^\d{5}$', message="Le code postal doit contenir 5 chiffres.")])
    ville = StringField('Ville')
    telephone = StringField('Téléphone')
    mail_contact = StringField('Mail de contact', validators=[Optional()])
    iban = StringField('IBAN')
    bic = StringField('BIC')
    logo = FileField('Logo')

    def validate_tva_intracommunautaire(form, field):
        if not form.exonere_tva.data and not field.data:
            raise ValidationError('Le numéro TVA intracommunautaire est requis si l\'organisation n\'est pas exonérée de TVA.')

class ClientForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    adresse = StringField('Adresse')
    code_postal = StringField('Code postal', validators=[Optional(), Regexp(r'^\d{5}$', message="Le code postal doit contenir 5 chiffres.")])
    ville = StringField('Ville')
    telephone = TelField('Téléphone')
    mail = EmailField('Email', validators=[Email(), DataRequired()])

""" class TransactionForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], default=date.today, widget=DateInput())
    type = SelectField('Type', choices=[('Entrée', 'Entrée'), ('Sortie', 'Sortie')], validators=[DataRequired()])
    # Utiliser FloatField pour le montant
    montant = FloatField('Montant', validators=[DataRequired(), NumberRange(min=0.01, message="Le montant doit être positif.")]) 
    description = TextAreaField('Description', validators=[Optional()]) # Utiliser TextAreaField pour plus d'espace
    mode_paiement = StringField('Mode de Paiement', validators=[Optional()])
    
    # Champ pour sélectionner un exercice existant (peut être vide si on en crée un nouveau)
    exercice_id = SelectField('Exercice Comptable', coerce=int, validators=[Optional()]) 

    compte_id = SelectField('Compte Comptable Associé', coerce=int, validators=[Optional()])
    
    # Champs pour créer un nouvel exercice (optionnels au niveau du formulaire, validés dans la vue si nécessaire)
    date_debut_exercice = DateField('Date de début du nouvel exercice', validators=[Optional()], widget=DateInput())
    date_fin_exercice = DateField('Date de fin du nouvel exercice', validators=[Optional()], widget=DateInput())
    
    # Champ caché pour indiquer si on crée un nouvel exercice (géré par JS)
    creer_nouvel_exercice = HiddenField(default='false') 

    submit = SubmitField('Ajouter la Transaction')

    # Initialisation dynamique des choix pour exercice_id
    def __init__(self, organisation_id=None, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        # Peupler les exercices
        default_exercice_choices = [(0, '--- Sélectionner un exercice ---')]
        if organisation_id:
            try:
                exercices = ExerciceComptable.query.filter_by(organisation_id=organisation_id).order_by(ExerciceComptable.date_debut.desc()).all()
                if exercices:
                     exercice_choices = [(ex.id, f"{ex.date_debut.strftime('%Y')} - {ex.date_fin.strftime('%Y')}") for ex in exercices]
                     self.exercice_id.choices = default_exercice_choices + exercice_choices
                else:
                     self.exercice_id.choices = [(0, '--- Aucun exercice existant ---')]
            except Exception as e:
                 print(f"Erreur lors de la récupération des exercices: {e}")
                 self.exercice_id.choices = [(0, '--- Erreur chargement exercices ---')]
        else:
             self.exercice_id.choices = [(0, '--- Organisation non spécifiée ---')]

        # --- NOUVEAU : Peupler les comptes comptables ---
        default_compte_choices = [(0, '--- Aucun compte sélectionné ---')] # 0 ou '' comme valeur pour "aucun"
        if organisation_id:
            try:
                comptes = CompteComptable.query.filter_by(organisation_id=organisation_id).order_by(CompteComptable.numero).all()
                if comptes:
                    compte_choices = [(c.id, f"{c.numero} - {c.nom}") for c in comptes]
                    self.compte_id.choices = default_compte_choices + compte_choices
                else:
                    self.compte_id.choices = [(0, '--- Aucun compte défini ---')]
            except Exception as e:
                print(f"Erreur lors de la récupération des comptes: {e}")
                self.compte_id.choices = [(0, '--- Erreur chargement comptes ---')]
        else:
            self.compte_id.choices = [(0, '--- Organisation non spécifiée ---')]
        
        # Assigner None si la valeur est 0 (pour nullable=True dans la DB)
        self.compte_id.pre_validate = lambda form: setattr(form.compte_id, 'data', form.compte_id.data if form.compte_id.data != 0 else None)

    # Validation personnalisée si nécessaire (exemple)
    def validate_nouvel_exercice(self, field):
        # Cette validation est un exemple, la logique principale sera dans la vue
        # car elle dépend de la valeur de creer_nouvel_exercice
        if self.creer_nouvel_exercice.data == 'true':
            if not self.date_debut_exercice.data or not self.date_fin_exercice.data:
                 raise ValidationError("Les dates de début et de fin sont requises pour créer un nouvel exercice.")
            if self.date_debut_exercice.data >= self.date_fin_exercice.data:
                 raise ValidationError("La date de début doit être antérieure à la date de fin.")
 """

class EntreeForm(FlaskForm):
    """Formulaire pour ajouter une transaction d'entrée (Revenu/Facture)."""
    # Champs communs
    date = DateField('Date', default=date.today, validators=[DataRequired()])
    montant = FloatField('Montant', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    mode_paiement = SelectField('Mode de Paiement', choices=[
        ('', '-- Sélectionner --'),
        ('Virement', 'Virement'),
        ('Chèque', 'Chèque'),
        ('Carte', 'Carte bancaire'),
        ('Espèces', 'Espèces'),
        ('Autre', 'Autre')
    ], validators=[Optional()]) # Optionnel ou requis selon tes besoins
    
    # Compte comptable (filtré pour Classe 7 - Produits)
    compte_id = QuerySelectField(
        'Compte de Produit',
        query_factory=lambda: [], # Sera peuplé dynamiquement dans __init__
        get_label=lambda compte: f"{compte.numero} - {compte.nom}",
        allow_blank=False, # Rendre la sélection obligatoire
        validators=[DataRequired(message="Veuillez sélectionner un compte de produit.")]
    )

    # Champs pour l'exercice comptable (identiques à TransactionForm)
    exercice_id = QuerySelectField(
        'Exercice Comptable Existant',
        query_factory=lambda: [], # Sera peuplé dynamiquement
        get_label=lambda ex: f"{ex.date_debut.strftime('%d/%m/%Y')} - {ex.date_fin.strftime('%d/%m/%Y')} ({ex.statut})",
        allow_blank=True, # Permettre de choisir "Créer nouveau"
        blank_text='-- Sélectionner ou Créer --',
        validators=[Optional()] # Optionnel car on peut créer un nouveau
    )
    creer_nouvel_exercice = HiddenField(default='false') # Champ caché pour le switch JS
    date_debut_exercice = DateField('Date de début (Nouvel Exercice)', validators=[Optional()])
    date_fin_exercice = DateField('Date de fin (Nouvel Exercice)', validators=[Optional()])

    submit = SubmitField('Ajouter Entrée')

    # Constructeur pour peupler dynamiquement les exercices (identique à TransactionForm)
    def __init__(self, organisation_id=None, *args, **kwargs):
        super(EntreeForm, self).__init__(*args, **kwargs)
        if organisation_id:
            self.exercice_id.query_factory = lambda: ExerciceComptable.query.filter_by(
                organisation_id=organisation_id
            ).order_by(ExerciceComptable.date_debut.desc()).all()
            # --- Ajout pour peupler les comptes comptables dynamiquement ---
            self.compte_id.query_factory = lambda: CompteComptable.query.filter(
                CompteComptable.organisation_id == organisation_id, # Filtrer par l'organisation
                CompteComptable.type == ClasseCompte.CLASSE_7,      # Filtrer par Classe 7
                CompteComptable.actif == True
            ).order_by(CompteComptable.numero).all()
            # -------------------------------------------------------------


class SortieForm(FlaskForm):
    """Formulaire pour ajouter une transaction de sortie (Dépense)."""
    # Champs communs (identiques à EntreeForm)
    date = DateField('Date', default=date.today, validators=[DataRequired()])
    montant = FloatField('Montant', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    mode_paiement = SelectField('Mode de Paiement', choices=[
        ('', '-- Sélectionner --'),
        ('Virement', 'Virement'),
        ('Chèque', 'Chèque'),
        ('Carte', 'Carte bancaire'),
        ('Espèces', 'Espèces'),
        ('Autre', 'Autre')
    ], validators=[Optional()])

    # Compte comptable (filtré pour Classe 6 - Charges)
    compte_id = QuerySelectField(
        'Compte de Charge',
        query_factory=lambda: [],
        get_label=lambda compte: f"{compte.numero} - {compte.nom}",
        allow_blank=False, # Rendre la sélection obligatoire
        validators=[DataRequired(message="Veuillez sélectionner un compte de charge.")]
    )

    # Champs pour l'exercice comptable (identiques à EntreeForm)
    exercice_id = QuerySelectField(
        'Exercice Comptable Existant',
        query_factory=lambda: [], # Sera peuplé dynamiquement
        get_label=lambda ex: f"{ex.date_debut.strftime('%d/%m/%Y')} - {ex.date_fin.strftime('%d/%m/%Y')} ({ex.statut})",
        allow_blank=True,
        blank_text='-- Sélectionner ou Créer --',
        validators=[Optional()]
    )
    creer_nouvel_exercice = HiddenField(default='false')
    date_debut_exercice = DateField('Date de début (Nouvel Exercice)', validators=[Optional()])
    date_fin_exercice = DateField('Date de fin (Nouvel Exercice)', validators=[Optional()])

    # Champ pour la pièce jointe (optionnel)
    attachment = FileField('Pièce Jointe (Facture)', validators=[
         Optional(), # Rend le champ optionnel
         FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Seuls les images (jpg, png, gif) et PDF sont autorisés !')
     ])

    submit = SubmitField('Ajouter Dépense')

    # Constructeur pour peupler dynamiquement les exercices et comptes (identique à EntreeForm mais filtre Classe 6)
    def __init__(self, organisation_id=None, *args, **kwargs):
        super(SortieForm, self).__init__(*args, **kwargs)
        if organisation_id:
            self.exercice_id.query_factory = lambda: ExerciceComptable.query.filter_by(
                organisation_id=organisation_id
            ).order_by(ExerciceComptable.date_debut.desc()).all()
            # --- Ajout pour peupler les comptes comptables dynamiquement ---
            self.compte_id.query_factory = lambda: CompteComptable.query.filter(
                CompteComptable.organisation_id == organisation_id, # Filtrer par l'organisation
                CompteComptable.type == ClasseCompte.CLASSE_6,      # Filtrer par Classe 6
                CompteComptable.actif == True
            ).order_by(CompteComptable.numero).all()
            # -------------------------------------------------------------

class CompteComptableForm(FlaskForm):
    # Champ caché pour l'ID lors de l'édition
    id = HiddenField('ID')

    numero = StringField('Numéro de compte',
                         validators=[DataRequired("Le numéro de compte est requis."),
                                     Length(min=1, max=20, message="Le numéro doit contenir entre 1 et 20 caractères.")])
    nom = StringField('Intitulé du compte',
                      validators=[DataRequired("L'intitulé est requis."),
                                  Length(min=3, max=150, message="L'intitulé doit contenir entre 3 et 150 caractères.")])

    # Utiliser l'Enum pour peupler les choix du SelectField
    type = SelectField('Classe',
                       # Utiliser la valeur (code 'C1') comme clé interne/soumise
                       # Utiliser le label pour l'affichage utilisateur
                       choices=[(choice.value, choice.label) for choice in ClasseCompte],
                       validators=[DataRequired("La classe est requise.")])


    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])

    solde_initial = FloatField('Solde Initial',
                               default=0.0,
                               validators=[Optional(), NumberRange(message="Le solde doit être un nombre.")]) # Rendre optionnel si 0 est acceptable par défaut

    submit = SubmitField('Enregistrer')

    # On ne met pas 'actif' ici, car on le gère avec un bouton séparé.
    # On ne met pas 'organisation_id' ici, car on l'ajoutera dans la route.

    # --- NOUVEAU FORMULAIRE : Ajouter/Modifier un Membre d'Équipe ---
class EquipeMembreForm(FlaskForm):
    """Formulaire pour ajouter un membre à l'équipe d'un projet."""
    # Champ caché pour le token CSRF
    csrf_token = HiddenField()

    # Sélectionner un utilisateur existant (optionnel)
    # Les 'choices' seront peuplées dynamiquement dans la route
    user_id = SelectField(
        'Utilisateur existant (Optionnel)',
        coerce=coerce_int_or_none, 
        validators=[Optional()] # Ce champ n'est pas obligatoire
    )

    # Nom du membre (obligatoire si aucun utilisateur n'est sélectionné, sinon pré-rempli)
    nom = StringField(
        'Nom du membre',
        validators=[
            Optional(), # Rendre optionnel ici, la logique de remplissage/validation est dans la route
            Length(max=100)
        ]
    )

    # Email du membre (toujours obligatoire pour la communication)
    email = StringField(
        'Email du membre',
        validators=[
            DataRequired(message="L'email est obligatoire."),
            Email(message="Veuillez entrer une adresse email valide."),
            Length(max=120)
        ]
    )

    # Rôle spécifique dans le projet (optionnel)
    role_projet = StringField(
        'Rôle dans le projet',
        validators=[Optional(), Length(max=80)]
    )

    submit = SubmitField('Ajouter le membre')

    # --- Validation personnalisée (optionnelle mais recommandée) ---
    def validate(self, extra_validators=None):
        # Exécuter les validateurs standards d'abord
        initial_validation = super(EquipeMembreForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        # Si aucun utilisateur n'est sélectionné, le nom devient obligatoire
        if not self.user_id.data and not self.nom.data:
            self.nom.errors.append('Le nom est obligatoire si vous ne sélectionnez pas un utilisateur existant.')
            return False

        # Si un utilisateur est sélectionné, mais que le nom et l'email sont aussi fournis,
        # on pourrait choisir de prioriser l'utilisateur sélectionné (logique déjà dans la route).
        # Ou ajouter une validation ici si nécessaire.

        return True
    
class NoteReunionForm(FlaskForm):
    # Utilise DateTimeLocalField pour un sélecteur de date/heure sympa
    date = DateField('Date de début', validators=[DataRequired()])
    # Le contenu sera géré par le Rich Text Editor, mais on utilise TextAreaField
    contenu = TextAreaField('Contenu de la note', validators=[DataRequired()])
    submit = SubmitField('Enregistrer la note')

# --- Formulaire pour la question du Chatbot ---
class ChatbotQuestionForm(FlaskForm):
    question = StringField(
        'Votre question',
        validators=[DataRequired("Veuillez entrer une question.")],
        render_kw={
            "placeholder": "Ex: Comment créer une facture ?",
            "aria-label": "Question pour le chatbot",
            "class": "form-control" # Classe Bootstrap pour le style
        }
    )
    # Pas besoin de SubmitField si on garde le bouton HTML existant
    # submit = SubmitField('Envoyer', render_kw={"class": "btn btn-outline-secondary"})