# c:\wamp\www\mon_compta_app\models\projets.py
from controllers.db_manager import db
from datetime import datetime
from sqlalchemy import Numeric


class Projet(db.Model):
    __tablename__ = 'projet'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    statut = db.Column(db.String(20), default="En attente")
    prix_total = db.Column(db.Numeric(precision=10, scale=2), nullable=False, default=0.0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    description_test = db.Column(db.String(200), nullable=True) # Ajout pour test

    # Foreign keys
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('app_user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)

    organisation = db.relationship('Organisation', back_populates='projets')
    user = db.relationship('User', back_populates='projets')

    transactions = db.relationship('FinancialTransaction', back_populates='projet', lazy='select', cascade="all, delete-orphan")
    client = db.relationship('Client', back_populates='projets', lazy='select')
    phases = db.relationship('Phase', back_populates='projet', lazy='select', cascade="all, delete-orphan")
    jalons = db.relationship('Jalon', back_populates='projet', lazy='select', cascade="all, delete-orphan")
    whiteboard = db.relationship('Whiteboard', back_populates='projet', uselist=False, lazy='select', cascade="all, delete-orphan")

    membres = db.relationship(
        'EquipeMembre',
        back_populates='projet',
        lazy='select', 
        cascade='all, delete-orphan'
    )

    notes_reunion = db.relationship(
        'NoteReunion',
        back_populates='projet', # Pointe vers l'attribut 'projet' dans NoteReunion
        lazy='dynamic', # 'dynamic' est bien si tu veux pouvoir filtrer/compter sans tout charger
        cascade='all, delete-orphan' # Supprime les notes si le projet est supprimé
    )
    def get_total(self):
        """Calculates the total amount of the project."""
        return self.prix_total

    def __repr__(self):
        return f'<Projet {self.nom}>'
