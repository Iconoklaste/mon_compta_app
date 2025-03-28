# c:\wamp\www\mon_compta_app\models\users.py

from controllers.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    

    projets = db.relationship('Projet', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.mail}>'
