# models/compte_comptable.py
import enum
from controllers.db_manager import db
from sqlalchemy import UniqueConstraint, Enum as DBEnum, Numeric 
import decimal
from sqlalchemy import func # Pour utiliser les fonctions d'agrégation SQL comme SUM
from sqlalchemy.orm import column_property # column_property n'est pas utilisé ici, mais func oui
from .ecritures_comptable import LigneEcriture, EcritureComptable # Importer les modèles liés
from .exercices import ExerciceComptable # Importer ExerciceComptable
from datetime import date # Pour la date du jour si besoin

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
    solde_initial = db.Column(db.Numeric(precision=10, scale=2), nullable=False, default=decimal.Decimal('0.00'))
    actif = db.Column(db.Boolean, nullable=False, default=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=False)
    organisation = db.relationship('Organisation', back_populates='plan_comptable')
    transactions = db.relationship('FinancialTransaction', back_populates='compte', lazy='dynamic')
    client_associe = db.relationship("Client", back_populates="compte_comptable", foreign_keys="Client.compte_comptable_id", uselist=False)
    lignes_ecriture = db.relationship("LigneEcriture", back_populates="compte", lazy="dynamic")


    __table_args__ = (UniqueConstraint('numero', 'organisation_id', name='uq_compte_numero_organisation'),)

    def calculer_solde_actuel(self, exercice: ExerciceComptable = None):
        """
        Calcule le solde actuel du compte pour un exercice donné (ou l'exercice courant par défaut).
        Solde = Solde Initial + SUM(Débits) - SUM(Crédits) sur l'exercice.

        Args:
            exercice: L'objet ExerciceComptable pour lequel calculer le solde.
                      Si None, tente de déterminer l'exercice courant (logique à affiner).

        Returns:
            float: Le solde calculé.
        """
        session = db.session # Accéder à la session SQLAlchemy

        # 1. Déterminer l'exercice pertinent
        if exercice is None:
            # Logique pour trouver l'exercice "en cours" pour cette organisation
            # Exemple simple : prendre le dernier exercice ouvert basé sur la date de fin
            # ATTENTION: Cette logique peut devoir être adaptée à ton application !
            exercice = session.query(ExerciceComptable).filter(
                ExerciceComptable.organisation_id == self.organisation_id,
                ExerciceComptable.statut == "Ouvert",
                ExerciceComptable.date_fin >= date.today() # Hypothèse simple
            ).order_by(ExerciceComptable.date_debut.asc()).first()

            # S'il n'y a pas d'exercice ouvert "futur", prendre le dernier ouvert
            if not exercice:
                 exercice = session.query(ExerciceComptable).filter(
                    ExerciceComptable.organisation_id == self.organisation_id,
                    ExerciceComptable.statut == "Ouvert"
                ).order_by(ExerciceComptable.date_fin.desc()).first()
                 
        solde_initial_decimal = self.solde_initial if self.solde_initial is not None else decimal.Decimal('0.00')

        if not exercice:
            # Si aucun exercice n'est trouvé, on ne peut pas calculer le solde actuel pertinent
            # On pourrait retourner le solde initial ou 0.0, ou lever une erreur.
            # Retournons le solde initial pour l'instant.
            return solde_initial_decimal

        # 2. Calculer la somme des débits et crédits pour ce compte DANS cet exercice
        # On joint LigneEcriture avec EcritureComptable pour filtrer par date_ecriture
        resultats = session.query(
            func.sum(LigneEcriture.montant_debit).label('total_debit'),
            func.sum(LigneEcriture.montant_credit).label('total_credit')
        ).join(EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id)\
        .filter(
            LigneEcriture.compte_id == self.id,
            EcritureComptable.exercice_id == exercice.id # Filtrer par l'exercice
            # Optionnel: Filtrer par date si l'exercice n'est pas la seule limite
            # EcritureComptable.date_ecriture >= exercice.date_debut,
            # EcritureComptable.date_ecriture <= exercice.date_fin
        ).one() # one() car on s'attend à une seule ligne de résultat (les totaux)

        total_debit_exercice = resultats.total_debit or decimal.Decimal('0.00')
        total_credit_exercice = resultats.total_credit or decimal.Decimal('0.00')


        # 3. Calculer le solde final
        # Note: La nature du solde (débiteur/créditeur) dépend de la classe du compte,
        # mais ici on calcule le solde net.
        solde_actuel = solde_initial_decimal + total_debit_exercice - total_credit_exercice

        return solde_actuel

    # Optionnel: Créer une propriété qui appelle la méthode sans argument
    # pour une utilisation plus simple dans les templates (utilise l'exercice par défaut)
    @property
    def solde_actuel_exercice_courant(self) -> decimal.Decimal: # Type de retour Decimal
         """ Propriété pour obtenir le solde de l'exercice courant (utilise la logique par défaut). """
         return self.calculer_solde_actuel()


    def __repr__(self):
        statut = "Actif" if self.actif else "Inactif"
        # Utiliser le label pour l'affichage
        type_str = self.type.label if self.type else "N/A"
        return f'<CompteComptable {self.numero} - {self.nom} (Classe: {type_str}, Statut: {statut})>'

