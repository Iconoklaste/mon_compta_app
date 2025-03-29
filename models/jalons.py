# c:\wamp\www\mon_compta_app\models\jalons.py

from controllers.db_manager import db

class Jalon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    atteint = db.Column(db.Boolean, default=False)
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=False)
    projet = db.relationship('Projet', backref=db.backref('jalons', lazy=True))

    def __repr__(self):
        return f"<Jalon {self.nom}>"
