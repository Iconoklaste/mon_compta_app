from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange
from datetime import date

class ProjetForm(FlaskForm):
    nom = StringField('Nom du projet', validators=[DataRequired()])
    client = StringField('Client', validators=[DataRequired()])
    date_debut = DateField('Date de début', default=date.today())
    date_fin = DateField('Date de fin')
    statut = SelectField('Statut', choices=[('En attente', 'En attente'), ('En cours', 'En cours'), ('Terminé', 'Terminé')], default='En attente')
    prix_total = IntegerField('Prix total', validators=[DataRequired(), NumberRange(min=0)])
