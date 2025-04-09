# c:\wamp\www\mon_compta_app\models\transactions.py
from controllers.db_manager import db
from datetime import date
from .compte_comptable import CompteComptable # Importer le modèle

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # Use db.Date
    type = db.Column(db.String(10), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    mode_paiement = db.Column(db.String(50))
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    exercice_id = db.Column(db.Integer, db.ForeignKey('exercice_comptable.id'), nullable=True)
    reglement = db.Column(db.String(20), default="Non réglée") # Add this line
    compte_id = db.Column(db.Integer, db.ForeignKey('compte_comptable.id'), nullable=False)
    compte = db.relationship('CompteComptable', back_populates='transactions')

    def __repr__(self):
        return f'<Transaction {self.description}>'
