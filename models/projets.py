# c:\wamp\www\mon_compta_app\models\projets.py
from controllers.db_manager import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Projet(db.Model):
    __tablename__ = 'projet'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    statut = db.Column(db.String(20), default="En attente")
    prix_total = db.Column(db.Float, nullable=False, default=0.0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)

    transactions = db.relationship('Transaction', backref='projet', lazy='select', cascade="all, delete-orphan")
    client = db.relationship('Client', back_populates='projets', lazy='select')
    phases = db.relationship('Phase', back_populates='projet', lazy='select', cascade="all, delete-orphan")
    jalons = db.relationship('Jalon', back_populates='projet', lazy='select', cascade="all, delete-orphan")
    whiteboard = db.relationship('Whiteboard', back_populates='projet', uselist=False, lazy='select', cascade="all, delete-orphan")

    membres = relationship(
        'EquipeMembre',
        back_populates='projet',
        lazy='select', 
        cascade='all, delete-orphan'
    )

    def get_total(self):
        """Calculates the total amount of the project."""
        return self.prix_total

    def __repr__(self):
        return f'<Projet {self.nom}>'
