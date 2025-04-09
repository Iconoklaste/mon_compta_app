# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import (HiddenField, StringField, DateField, 
                     widgets, SelectField, IntegerField, 
                     BooleanField, SubmitField, FieldList, 
                     FormField, FloatField, TextAreaField, PasswordField, EmailField, 
                     TelField, FileField)
from wtforms.validators import (DataRequired, Email, Optional, 
                                EqualTo, Regexp, ValidationError,
                                NumberRange, Length)
from models.clients import Client
from models.organisations import Organisation
from models.exercices import ExerciceComptable
from models import CompteComptable
from models.compte_comptable import ClasseCompte

from datetime import date

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
    nom = StringField('Nom', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], widget=DateInput())
    atteint = BooleanField('Atteint')

class PhaseForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    date_debut = DateField('Date de début', default=date.today)
    date_fin = DateField('Date de fin', default=date.today)
    statut = SelectField('Statut', choices=[('En cours', 'En cours'), ('Terminée', 'Terminée'), ('En attente', 'En attente')])
    jalons = FieldList(FormField(JalonForm), min_entries=1)  # Add this line
    submit = SubmitField('Enregistrer')

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

class TransactionForm(FlaskForm):
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