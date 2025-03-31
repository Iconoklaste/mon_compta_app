# c:\wamp\www\mon_compta_app\models\whiteboard.py
from controllers.db_manager import db
from datetime import datetime, timezone

class Whiteboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)  # Store whiteboard data as JSON string
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id', name='fk_whiteboard_projet', ondelete="CASCADE"), nullable=False)
    projet = db.relationship('Projet', back_populates='whiteboard', lazy='select') # Add back_populates
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Whiteboard {self.id} for Projet {self.projet_id}>"
