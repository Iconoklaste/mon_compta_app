# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired
from models.clients import Client

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
