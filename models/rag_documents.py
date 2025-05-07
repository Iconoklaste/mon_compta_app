# Dans votre fichier models.py (ou équivalent)
from controllers.db_manager import db
from datetime import datetime

class RagDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False) # Nom du fichier tel qu'uploadé
    # stored_filename = db.Column(db.String(255), nullable=False, unique=True) # Si vous renommez les fichiers pour le stockage
    indexed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Indexé') # Ex: 'Indexé', 'Erreur', 'En attente d'indexation'
    # Optionnel: stocker les IDs des vecteurs si votre vector store le permet pour une suppression ciblée
    # vector_ids = db.Column(db.JSON) 

    projet = db.relationship('Projet', backref=db.backref('rag_documents', lazy='dynamic')) # ou lazy=True

    def __repr__(self):
        return f'<RagDocument {self.id} - {self.original_filename} (Projet {self.projet_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.original_filename,
            'indexed_at': self.indexed_at.isoformat() + "Z" if self.indexed_at else None, # Format ISO 8601 pour JS
            'status': self.status,
            'projet_id': self.projet_id
        }
