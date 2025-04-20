# c:\wamp\www\mon_compta_app\models\clients.py
from controllers.db_manager import db
from sqlalchemy import ForeignKey
# Assure-toi que CompteComptable est importable depuis ici
from .compte_comptable import CompteComptable
from .organisations import Organisation

class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(5))
    ville = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    mail = db.Column(db.String(100))

        # --- AJOUT : Lien vers l'Organisation ---
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    # Relation vers l'objet Organisation
    # Le backref permet d'accéder aux clients depuis une organisation (orga.clients)
    organisation = db.relationship("Organisation", back_populates="clients") # Changé pour back_populates
    # --- FIN AJOUT ---

    compte_comptable_id = db.Column(db.Integer, db.ForeignKey('compte_comptable.id'), nullable=True, unique=True)
    compte_comptable = db.relationship("CompteComptable", back_populates="client_associe", foreign_keys=[compte_comptable_id], uselist=False) # Changé pour back_populates, ajouté uselist=False explicitement

    projets = db.relationship('Projet', back_populates='client', lazy=True) # change backref to back_populates

    def __repr__(self):
        orga_info = f" (Orga ID: {self.organisation_id})" if self.organisation_id else ""
        return f'<Client {self.id} - {self.nom}{orga_info}>'
