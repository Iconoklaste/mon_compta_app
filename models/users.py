# c:\wamp\www\mon_compta_app\models\users.py

from controllers.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash
# from sqlalchemy import Index # Plus besoin d'importer Index ici

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)

    # --- Nouveaux champs ---
    is_super_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    # Rôle : chaîne simple pour flexibilité (prédéfini ou personnalisé)
    role = db.Column(db.String(50), nullable=False, default='Membre')
    # --- Fin des nouveaux champs ---

    projets = db.relationship('Projet', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    # --- Contrainte spécifique à PostgreSQL retirée ---
    # __table_args__ = (
    #     Index('uq_one_super_admin', 'is_super_admin', unique=True, postgresql_where=(is_super_admin == True)),
    # )
    # --- Fin de la contrainte retirée ---


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # S'assurer que password_hash n'est pas None avant de vérifier
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    def __repr__(self):
        role_info = f" ({self.role})"
        if self.is_super_admin:
            role_info = " (Super Admin)"
        elif self.is_demo:
            role_info += " [Demo]"
        return f'<User {self.mail}{role_info}>'

