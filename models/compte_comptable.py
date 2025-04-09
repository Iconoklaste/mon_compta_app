# models/compte_comptable.py
import enum
from controllers.db_manager import db
from sqlalchemy import UniqueConstraint, Enum as DBEnum
from sqlalchemy.orm import relationship

# Définir l'énumération pour les classes de compte
class ClasseCompte(enum.Enum):
    # La valeur (ex: 'C1') sera stockée en base.
    # Le label est pour l'affichage.
    CLASSE_1 = ('C1', "Classe 1 – les comptes de capitaux")
    CLASSE_2 = ('C2', "Classe 2 – les comptes d'immobilisations")
    CLASSE_3 = ('C3', "Classe 3 – les stocks et en-cours")
    CLASSE_4 = ('C4', "Classe 4 – les comptes de tiers")
    CLASSE_5 = ('C5', "Classe 5 – les comptes financiers")
    CLASSE_6 = ('C6', "Classe 6 – les comptes de charge")
    CLASSE_7 = ('C7', "Classe 7 – les comptes de produit")
    CLASSE_8 = ('C8', "Classe 8 – les comptes spéciaux")

    def __init__(self, code, label):
        """Initialiseur pour assigner code et label."""
        self._code = code
        self._label = label

    @property
    def code(self):
        """Retourne le code court (ex: 'C1')."""
        return self._code

    @property
    def label(self):
        """Retourne le libellé descriptif (modifiable ici si besoin)."""
        return self._label

    # Gardons les anciennes propriétés si tu les utilises ailleurs,
    # mais basées sur le label maintenant.
    @property
    def numero(self):
        """Retourne le numéro extrait du label (ex: '1')."""
        try:
            return self.label.split(' ')[1]
        except IndexError:
            return None # Ou gérer l'erreur autrement

    @property
    def nom_classe(self):
        """Retourne le nom de la classe extrait du label."""
        try:
            return self.label.split('–')[1].strip()
        except IndexError:
            return self.label # Retourne le label complet si le format change

    # Important pour que SQLAlchemy sache quoi stocker
    # (on stocke le code 'C1', 'C2', etc.)
    @property
    def value(self):
        return self.code

    # Permet de retrouver l'enum à partir du code stocké en DB (ex: 'C1')
    @classmethod
    def get_by_code(cls, code):
        for member in cls:
            if member.code == code:
                return member
        raise ValueError(f"Code de classe invalide: {code}")

class CompteComptable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    nom = db.Column(db.String(150), nullable=False)
    # Utiliser DBEnum pour stocker la VALEUR de l'énumération (le code 'C1', 'C2'...)
    # 'native_enum=False' est souvent recommandé pour la portabilité entre SGBD
    type = db.Column(DBEnum(ClasseCompte,
                              name="classe_compte_enum",
                              values_callable=lambda obj: [item.code for item in obj], # Stocke les codes 'C1', 'C2'...
                              native_enum=False), # Important pour stocker la chaîne 'C1'
                      nullable=False)
    description = db.Column(db.Text, nullable=True)
    solde_initial = db.Column(db.Float, nullable=False, default=0.0)
    actif = db.Column(db.Boolean, nullable=False, default=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    organisation = relationship('Organisation', backref=db.backref('plan_comptable', lazy='dynamic'))
    transactions = relationship('Transaction', back_populates='compte', lazy='dynamic')

    __table_args__ = (UniqueConstraint('numero', 'organisation_id', name='uq_compte_numero_organisation'),)

    def __repr__(self):
        statut = "Actif" if self.actif else "Inactif"
        # Utiliser le label pour l'affichage
        type_str = self.type.label if self.type else "N/A"
        return f'<CompteComptable {self.numero} - {self.nom} (Classe: {type_str}, Statut: {statut})>'

