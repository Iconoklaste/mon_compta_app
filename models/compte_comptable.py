# models/compte_comptable.py
import enum # Importer le module enum
from controllers.db_manager import db
from sqlalchemy import UniqueConstraint, Enum as DBEnum # Importer Enum de SQLAlchemy
from sqlalchemy.orm import relationship # Importer relationship explicitement

# Définir l'énumération pour les classes de compte
class ClasseCompte(enum.Enum):
    CLASSE_1 = "Classe 1 – les comptes de capitaux"
    CLASSE_2 = "Classe 2 – les comptes d'immobilisations"
    CLASSE_3 = "Classe 3 – les stocks et en-cours"
    CLASSE_4 = "Classe 4 – les comptes de tiers"
    CLASSE_5 = "Classe 5 – les comptes financiers"
    CLASSE_6 = "Classe 6 – les comptes de charge"
    CLASSE_7 = "Classe 7 – les comptes de produit"
    CLASSE_8 = "Classe 8 – les comptes spéciaux"

    # Optionnel: une méthode pour obtenir juste le numéro ou le nom si besoin
    @property
    def numero(self):
        return self.value.split(' ')[1] # Retourne "1", "2", etc.

    @property
    def nom_classe(self):
        return self.value.split('–')[1].strip() # Retourne "les comptes de capitaux", etc.

class CompteComptable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False) # Numéro du compte (ex: "607", "411000")
    nom = db.Column(db.String(150), nullable=False) # Nom du compte (ex: "Achats de marchandises", "Clients - Dupont")
    # Utiliser DBEnum pour stocker la valeur de l'énumération ClasseCompte
    type = db.Column(DBEnum(ClasseCompte, name="classe_compte_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    description = db.Column(db.Text, nullable=True) # Description optionnelle
    solde_initial = db.Column(db.Float, nullable=False, default=0.0) # Solde initial du compte
    actif = db.Column(db.Boolean, nullable=False, default=True) # Renommé 'etat' en 'actif'

    # Clé étrangère vers l'organisation : Chaque organisation a son propre plan
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)

    # Relation inverse pour accéder facilement aux comptes depuis une organisation
    organisation = relationship('Organisation', backref=db.backref('plan_comptable', lazy='dynamic'))

    # Relation pour lier les transactions à ce compte
    # Assurez-vous que le modèle Transaction a bien 'compte = relationship("CompteComptable", backref="transactions")'
    transactions = relationship('Transaction', backref='compte', lazy='dynamic') # Utilisation de backref pour correspondre à Transaction

    # Contrainte d'unicité : Le numéro de compte doit être unique PAR organisation
    __table_args__ = (UniqueConstraint('numero', 'organisation_id', name='uq_compte_numero_organisation'),)

    def __repr__(self):
        statut = "Actif" if self.actif else "Inactif"
        # Accéder à la valeur de l'énumération avec .value si l'objet est chargé
        type_str = self.type.value if self.type else "N/A"
        return f'<CompteComptable {self.numero} - {self.nom} (Classe: {type_str}, Statut: {statut})>'

