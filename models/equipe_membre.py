# c:\wamp\www\mon_compta_app\models\equipe_membre.py

from controllers.db_manager import db


class EquipeMembre(db.Model):
    __tablename__ = 'equipe_membre'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False) # Nom complet du membre
    email = db.Column(db.String(120), nullable=False) # Email pour la communication
    role_projet = db.Column(db.String(80), nullable=True) # Rôle spécifique dans CE projet

    # Clé étrangère vers le projet
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id', ondelete='CASCADE'), nullable=False)
    # Relation vers le projet (Many-to-One)
    projet = db.relationship('Projet', back_populates='membres')

    # Clé étrangère vers l'utilisateur (optionnelle)
    user_id = db.Column(db.Integer, db.ForeignKey('app_user.id', ondelete='SET NULL'), nullable=True)
    # Relation vers l'utilisateur (Many-to-One)
    user = db.relationship('User', back_populates='participations_projet')

    def __repr__(self):
        user_info = f" (User ID: {self.user_id})" if self.user_id else " (Externe)"
        return f'<EquipeMembre {self.nom} - Projet ID: {self.projet_id}{user_info}>'

