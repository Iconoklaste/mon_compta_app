# c:\wamp\www\mon_compta_app\models\phases.py

from controllers.db_manager import db

class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    statut = db.Column(db.String(50), default="En cours")  # e.g., "En cours", "Terminée", "En attente"
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=False)
    projet = db.relationship('Projet', backref=db.backref('phases', lazy=True))

    def __repr__(self):
        return f"<Phase {self.nom}>"
