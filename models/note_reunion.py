# c:\wamp\www\mon_compta_app\models\note_reunion.py
from controllers.db_manager import db # Assure-toi que l'import est correct
from datetime import datetime, timezone


def get_naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class NoteReunion(db.Model):
    __tablename__ = 'notes_reunion' # Nom de la table

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    contenu = db.Column(db.Text, nullable=False) # Utilise Text pour du contenu long (HTML)
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id', ondelete="CASCADE"), nullable=False) # Ajout de ondelete="CASCADE"
    created_at = db.Column(db.DateTime, default=get_naive_utc_now) # Utilise la fonction helper
    updated_at = db.Column(db.DateTime, default=get_naive_utc_now, onupdate=get_naive_utc_now)

    # --- AJOUT/MODIFICATION : Relation vers Projet ---
    projet = db.relationship(
        'Projet',
        back_populates='notes_reunion' # Pointe vers l'attribut 'notes_reunion' dans Projet
    )
    # -------------------------------------------------

    # Optionnel : Si tu veux associer à une phase
    # phase_id = db.Column(db.Integer, db.ForeignKey('project_phase.id'), nullable=True) # Nullable
    # phase = db.relationship('Phase', backref='notes_reunion') # Simple backref ici si Phase n'a pas besoin de back_populates

    def __repr__(self):
        return f'<NoteReunion {self.id} - Projet {self.projet_id}>'

