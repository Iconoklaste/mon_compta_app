# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, DateField, widgets, SelectField, IntegerField, BooleanField, SubmitField, FieldList, FormField, PasswordField, EmailField, TelField, FileField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, Regexp, ValidationError
from models.clients import Client
from models.organisations import Organisation
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
