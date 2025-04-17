# c:\wamp\www\mon_compta_app\models\jalons.py

from controllers.db_manager import db


class Jalon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    atteint = db.Column(db.Boolean, default=False)
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id', ondelete="CASCADE"), nullable=False)

    projet = db.relationship('Projet', back_populates='jalons', lazy='select') # Add back_populates
    phase_id = db.Column(db.Integer, db.ForeignKey('project_phase.id'), nullable=False)
    phase = db.relationship('Phase', back_populates='jalons')


    def __repr__(self):
        return f"<Jalon {self.nom}>"
