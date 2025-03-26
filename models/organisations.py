# c:\wamp\www\mon_compta_app\models\organisations.py

from controllers.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash

class Organisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    designation = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(5))  # Enforce 5-digit postal code
    ville = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    mail_contact = db.Column(db.String(100))
    logo = db.Column(db.String(200))  # Store the path to the logo image

    users = db.relationship('User', backref='organisation', lazy=True)
    projets = db.relationship('Projet', backref='organisation', lazy=True)
    transactions = db.relationship('Transaction', backref='organisation', lazy=True)

    def __repr__(self):
        return f'<Organisation {self.designation}>'
