# c:\wamp\www\mon_compta_app\models\users.py

from controllers.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'app_user'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='users')
    is_super_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(50), nullable=False, default='Membre')
    projets = db.relationship('Projet', back_populates='user', lazy=True)
    transactions = db.relationship('Transaction', back_populates='user', lazy=True)

    participations_projet = db.relationship(
        'EquipeMembre',
        back_populates='user',
        lazy='dynamic' # Permet de filtrer/compter sans tout charger
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # S'assurer que password_hash n'est pas None avant de vérifier
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def __repr__(self):
        role_info = f" ({self.role})"
        if self.is_super_admin:
            role_info = " (Super Admin)"
        elif self.is_demo:
            role_info += " [Demo]"
        return f'<User {self.mail}{role_info}>'

