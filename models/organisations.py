# c:\wamp\www\mon_compta_app\models\organisations.py

from controllers.db_manager import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates 
from flask import current_app

class Organisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    designation = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(200))
    code_postal = db.Column(db.String(5))  # Enforce 5-digit postal code
    ville = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    mail_contact = db.Column(db.String(100))
    logo = db.Column(db.LargeBinary)  # Store the logo image as binary data
    logo_mimetype = db.Column(db.String(50)) # Store the mimetype of the logo
    iban = db.Column(db.String(34))  # IBAN format: XX00 1234 5678 9012 3456 7890 (max 34 characters)
    bic = db.Column(db.String(11))  # BIC format: ABCD1234XXX (max 11 characters)
    exonere_tva = db.Column(db.Boolean, default=False)  # VAT exemption checkbox
    
    # New fields for accounting
    siret = db.Column(db.String(14), nullable=True, unique=True)  # SIRET is mandatory and unique
    tva_intracommunautaire = db.Column(db.String(20), unique=True)  # Optional VAT number
    forme_juridique = db.Column(db.String(50))  # Optional legal form

    users = db.relationship('User', back_populates='organisation', lazy=True) # Changé pour back_populates
    projets = db.relationship('Projet', back_populates='organisation', lazy=True) # Sera modifié ensuite
    transactions = db.relationship('FinancialTransaction', back_populates='organisation', lazy=True) # Changé pour back_populates
    clients = db.relationship("Client", back_populates="organisation", lazy="dynamic")
    plan_comptable = db.relationship("CompteComptable", back_populates="organisation", lazy="dynamic")
    ecritures_comptables = db.relationship("EcritureComptable", back_populates="organisation")
    exercices = db.relationship("ExerciceComptable", back_populates="organisation", lazy="dynamic", order_by="ExerciceComptable.date_debut") # lazy='dynamic' et order_by sont de bonnes options ici


    def __repr__(self):
        return f'<Organisation {self.designation}>'

    @validates('logo')
    def validate_logo(self, key, logo):
        """
        Validate the logo size before saving it to the database.
        """
        max_size = current_app.config.get('MAX_LOGO_SIZE', 1024 * 1024)  # 1MB default
        if logo and len(logo) > max_size:
            raise ValueError(f"Logo size exceeds the maximum allowed size of {max_size} bytes.")
        return logo
