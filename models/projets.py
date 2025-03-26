from controllers.db_manager import db
from datetime import date

class Projet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    client = db.Column(db.String(100), nullable=False)
    date_debut = db.Column(db.Date)  # Use db.Date
    date_fin = db.Column(db.Date)    # Use db.Date
    statut = db.Column(db.String(20), default="En attente")
    prix_total = db.Column(db.Integer, nullable=False, default=0)  # prix_total is now not nullable

    transactions = db.relationship('Transaction', backref='projet', lazy=True)

    def __repr__(self):
        return f'<Projet {self.nom}>'
