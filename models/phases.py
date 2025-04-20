# c:\wamp\www\mon_compta_app\models\phases.py
from controllers.db_manager import db

class Phase(db.Model):
    __tablename__ = 'project_phase'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    statut = db.Column(db.String(50), default="En cours")
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id', ondelete="CASCADE"), nullable=False)
    projet = db.relationship('Projet', back_populates='phases', lazy='select') # Add back_populates
    progress = db.Column(db.Integer, default=0)
    jalons = db.relationship('Jalon', back_populates='phase', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Phase {self.nom}>"
