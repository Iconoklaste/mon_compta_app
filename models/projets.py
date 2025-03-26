# c:\wamp\www\mon_compta_app\models\projets.py
from controllers.db_manager import db
from datetime import datetime

class Projet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    # client = db.Column(db.String(100), nullable=False) # Removed this line
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    statut = db.Column(db.String(20), default="En attente")
    prix_total = db.Column(db.Integer, nullable=False, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True) # Add this line

    transactions = db.relationship('Transaction', backref='projet', lazy=True)

    def __repr__(self):
        return f'<Projet {self.nom}>'
