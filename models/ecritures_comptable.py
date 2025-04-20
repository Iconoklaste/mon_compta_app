# models/ecritures_comptable.py
from datetime import date
from sqlalchemy import ForeignKey, CheckConstraint

from controllers.db_manager import db # Assure-toi que ce chemin d'import est correct
from sqlalchemy import Numeric
import decimal

class EcritureComptable(db.Model):
    """ Représente une écriture comptable globale (pièce comptable).
        Elle contient plusieurs lignes (débit/crédit) qui s'équilibrent.
    """
    __tablename__ = 'ecriture_comptable' # Nom explicite pour la table

    id = db.Column(db.Integer, primary_key=True)
    date_ecriture = db.Column(db.Date, nullable=False, default=date.today)
    libelle = db.Column(db.String(255), nullable=False)
    reference_origine = db.Column(db.String(100), nullable=True, index=True) # Ex: 'Transaction:123', 'Facture:45'

    # Clés étrangères
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    exercice_id = db.Column(db.Integer, db.ForeignKey('exercice_comptable.id'), nullable=False)

    # Relations
    # Une écriture a plusieurs lignes
    lignes = db.relationship(
        "LigneEcriture",
        back_populates="ecriture", # Lien bidirectionnel avec LigneEcriture
        cascade="all, delete-orphan", # Supprimer les lignes si l'écriture est supprimée
        
    )
    # Lien vers l'organisation (many-to-one)
    organisation = db.relationship("Organisation", back_populates="ecritures_comptables") # Changé pour back_populates
    # Lien vers l'exercice comptable (many-to-one)
    exercice = db.relationship("ExerciceComptable", back_populates="ecritures_comptables") # Sera modifié plus tard

    def __repr__(self):
        return f'<EcritureComptable ID:{self.id} - {self.libelle} ({self.date_ecriture})>'

    @property
    def total_debit(self):
        """ Calcule le total des débits pour cette écriture. """
        # Note: nécessite de charger les lignes. Peut être coûteux si appelé souvent.
        # Pourrait être optimisé avec une requête directe si besoin.
        return sum(ligne.montant_debit or decimal.Decimal(0) for ligne in self.lignes)


    @property
    def total_credit(self):
        """ Calcule le total des crédits pour cette écriture. """
        return sum(ligne.montant_credit or decimal.Decimal(0) for ligne in self.lignes)


    @property
    def est_equilibree(self):
        """ Vérifie si l'écriture est équilibrée (total débit == total crédit). """
        # Attention à la précision des flottants
        return self.total_debit == self.total_credit


class LigneEcriture(db.Model):
    """ Représente une ligne individuelle (mouvement) au sein d'une écriture comptable.
        Impacte un compte comptable spécifique en débit ou en crédit.
    """
    __tablename__ = 'ligne_ecriture' # Nom explicite pour la table

    id = db.Column(db.Integer, primary_key=True)
    montant_debit = db.Column(db.Numeric(precision=10, scale=2), nullable=True, default=decimal.Decimal(0)) # Changer Float en Numeric
    montant_credit = db.Column(db.Numeric(precision=10, scale=2), nullable=True, default=decimal.Decimal(0))
    libelle = db.Column(db.String(255), nullable=True) # Libellé spécifique à la ligne (optionnel)

    # Clés étrangères
    ecriture_id = db.Column(db.Integer, db.ForeignKey('ecriture_comptable.id'), nullable=False)
    compte_id = db.Column(db.Integer, db.ForeignKey('compte_comptable.id'), nullable=False)

    # Relations
    # Une ligne appartient à une seule écriture (many-to-one)
    ecriture = db.relationship("EcritureComptable", back_populates="lignes")
    # Une ligne concerne un seul compte comptable (many-to-one)
    # Ajout d'un backref pour pouvoir accéder aux lignes depuis un compte
    compte = db.relationship("CompteComptable", back_populates="lignes_ecriture")

    # Contrainte pour s'assurer qu'on a soit un débit, soit un crédit, mais pas les deux > 0
    # Et que les montants sont positifs ou nuls.
    __table_args__ = (
        CheckConstraint('montant_debit >= 0', name='chk_debit_non_negatif'),
        CheckConstraint('montant_credit >= 0', name='chk_credit_non_negatif'),
        CheckConstraint(
            '(montant_debit > 0 AND montant_credit = 0) OR (montant_credit > 0 AND montant_debit = 0) OR (montant_debit = 0 AND montant_credit = 0)',
            name='chk_debit_ou_credit_exclusif'
        ),
    )

    def __repr__(self):
        mouvement = f"Débit: {self.montant_debit}" if self.montant_debit else f"Crédit: {self.montant_credit}"
        compte_info = f"Compte ID:{self.compte_id}" if not self.compte else f"Compte:{self.compte.numero}"
        return f'<LigneEcriture ID:{self.id} - {compte_info} - {mouvement} (Ecriture ID:{self.ecriture_id})>'

