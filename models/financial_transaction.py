from controllers.db_manager import db
from sqlalchemy import Column, Integer, Date, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from .compte_comptable import CompteComptable

class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transaction'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # Use db.Date
    montant = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    description = db.Column(db.String(200))
    mode_paiement = db.Column(db.String(50))
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('app_user.id'), nullable=True)
    exercice_id = db.Column(db.Integer, db.ForeignKey('exercice_comptable.id'), nullable=True)
    reglement = db.Column(db.String(20), default="Non réglée") # Add this line
    compte_id = db.Column(db.Integer, db.ForeignKey('compte_comptable.id'), nullable=False)

    attachment_filename = db.Column(db.String(255), nullable=True) # Store the filename on the server
    attachment_mimetype = db.Column(db.String(100), nullable=True) # To store MIME type like 'image/png' or 'application/pdf'

    # **discriminator**
    trans_type    = Column(String(20)) # Temporarily nullable for migration
    __mapper_args__ = {
        'polymorphic_on': trans_type,
        'polymorphic_identity': 'base' # Identity for base class instances
    }

    # **relations**
    compte = db.relationship('CompteComptable', back_populates='transactions')
    organisation = db.relationship('Organisation', back_populates='transactions')
    user = db.relationship('User', back_populates='transactions')
    projet = db.relationship('Projet', back_populates='transactions')
    exercice = db.relationship('ExerciceComptable', back_populates='transactions')

    def __repr__(self):
        return f'<FinancialTransaction {self.description}>'

class Revenue(FinancialTransaction):
    __mapper_args__ = {
        'polymorphic_identity': 'revenue', # Identity for Revenue instances
    }


class Expense(FinancialTransaction):
    __mapper_args__ = {
        'polymorphic_identity': 'expense', # Identity for Expense instances
    }