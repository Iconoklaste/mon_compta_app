# c:\wamp\www\mon_compta_app\models\clients.py
from controllers.db_manager import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(5))
    ville = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    mail = db.Column(db.String(100))

    projets = db.relationship('Projet', backref='client_obj', lazy=True)

    def __repr__(self):
        return f'<Client {self.nom}>'
