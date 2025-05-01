# c:\wamp\www\mon_compta_app\models\exercices.py
from controllers.db_manager import db
from datetime import date

class ExerciceComptable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    statut = db.Column(db.String(20), default="Ouvert")  # Ou "Clôturé"
    
    # Nouvelle référence : chaque exercice est associé à une organisation
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='exercices')
    
    # Relation pour accéder aux transactions de cet exercice
    transactions = db.relationship('FinancialTransaction', back_populates='exercice', lazy=True)
    ecritures_comptables = db.relationship('EcritureComptable', back_populates='exercice', lazy='dynamic') # Ajout de lazy='dynamic' pour potentiellement gérer de nombreuses écritures

    def __repr__(self):
        return f'<ExerciceComptable {self.date_debut} - {self.date_fin}>'
