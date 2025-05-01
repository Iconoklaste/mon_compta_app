# utils/ecriture_comptable_util.py
from datetime import date
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
# Ajuste les chemins d'import si nécessaire par rapport à la position de 'utils'
from models import FinancialTransaction, Revenue, Expense, CompteComptable, EcritureComptable, LigneEcriture, Client, Organisation # Updated import
from models.compte_comptable import ClasseCompte
from controllers.db_manager import db # Pour accéder à la session db.session

# Configuration du logger pour cet utilitaire
logger = logging.getLogger(__name__)

# --- Constantes pour les numéros de compte par défaut ---
# Il serait idéal de les rendre configurables par organisation plus tard
COMPTE_BANQUE_DEFAUT = '51'
COMPTE_CLIENT_DEFAUT = '410'
# -------------------------------------------------------

def generer_ecriture_depuis_transaction(transaction: FinancialTransaction, session: Session = db.session):
    """
    Génère et enregistre une EcritureComptable équilibrée à partir d'une Transaction.

    Args:
        transaction: L'objet Transaction qui vient d'être créé/commité.
        session: La session SQLAlchemy à utiliser (par défaut, la session globale db.session).

    Returns:
        EcritureComptable: L'écriture comptable créée, ou None en cas d'erreur.
    """
    logger.info(f"Début de la génération d'écriture pour Transaction ID: {transaction.id}")

    if not transaction or not transaction.id:
        logger.error("Transaction invalide fournie pour la génération d'écriture.")
        return None

    organisation_id = transaction.organisation_id
    montant = transaction.montant
    date_transaction = transaction.date
    description_transaction = transaction.description
    exercice_id = transaction.exercice_id
    compte_principal_id = transaction.compte_id # Compte de charge (6) ou produit (7)

    compte_principal = session.get(CompteComptable, compte_principal_id)
    if not compte_principal:
        logger.error(f"Compte principal ID {compte_principal_id} non trouvé pour Transaction ID {transaction.id}.")
        # Que faire ? Lever une exception ? Retourner None ? Logguer et continuer ?
        # Pour l'instant, on loggue et on arrête pour cette transaction.
        return None

    compte_contrepartie = None
    compte_debit_id = None
    compte_credit_id = None

    try:
        if isinstance(transaction, Expense):
            # Dépense: Débit Compte Charge (6xx), Crédit Compte Banque (512)
            compte_debit_id = compte_principal.id
            compte_contrepartie = session.query(CompteComptable).filter_by(
                organisation_id=organisation_id,
                numero=COMPTE_BANQUE_DEFAUT
            ).first()
            if not compte_contrepartie:
                logger.error(f"Compte Banque par défaut '{COMPTE_BANQUE_DEFAUT}' non trouvé pour Organisation ID {organisation_id}.")
                return None # Arrêter si le compte banque manque
            compte_credit_id = compte_contrepartie.id
            libelle_ecriture = f"Dépense: {description_transaction}"

        elif isinstance(transaction, Revenue):
            # Revenu/Facture: Débit Compte Client (411), Crédit Compte Produit (7xx)
            compte_credit_id = compte_principal.id
            compte_contrepartie = session.query(CompteComptable).filter_by(
                organisation_id=organisation_id,
                numero=COMPTE_CLIENT_DEFAUT
            ).first()
            if not compte_contrepartie:
                logger.error(f"Compte Client par défaut '{COMPTE_CLIENT_DEFAUT}' non trouvé pour Organisation ID {organisation_id}.")
                return None # Arrêter si le compte client manque
            compte_debit_id = compte_contrepartie.id
            libelle_ecriture = f"Facture/Revenu: {description_transaction}"

        else:
            logger.warning(f"Type de transaction non géré '{transaction.trans_type}' pour Transaction ID {transaction.id}. Aucune écriture générée.")
            return None

        # --- Création de l'écriture et des lignes ---
        if compte_debit_id and compte_credit_id:
            # Créer l'écriture comptable globale
            nouvelle_ecriture = EcritureComptable(
                date_ecriture=date_transaction,
                libelle=libelle_ecriture[:255], # Tronquer si nécessaire
                reference_origine=f"Transaction:{transaction.id}",
                organisation_id=organisation_id,
                exercice_id=exercice_id
            )

            # Créer la ligne de débit
            ligne_debit = LigneEcriture(
                montant_debit=montant,
                montant_credit=0.0,
                compte_id=compte_debit_id,
                ecriture=nouvelle_ecriture # Lier directement à l'objet parent
            )

            # Créer la ligne de crédit
            ligne_credit = LigneEcriture(
                montant_debit=0.0,
                montant_credit=montant,
                compte_id=compte_credit_id,
                ecriture=nouvelle_ecriture # Lier directement à l'objet parent
            )

            # Ajouter les lignes à l'écriture (SQLAlchemy gère la relation)
            # Pas besoin de faire nouvelle_ecriture.lignes.append(...) explicitement
            # car on a lié via ecriture=nouvelle_ecriture dans les lignes.

            # Ajouter l'écriture (et ses lignes en cascade) à la session
            session.add(nouvelle_ecriture)
            # Le commit sera fait dans le contrôleur après l'appel de cette fonction

            logger.info(f"EcritureComptable ID (pré-commit): {nouvelle_ecriture} générée pour Transaction ID: {transaction.id}")
            return nouvelle_ecriture # Retourner l'objet créé

    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération de l'écriture pour Transaction ID {transaction.id}: {e}", exc_info=True)
        # Ne pas faire de rollback ici, le contrôleur s'en chargera si nécessaire.
        return None

    return None # Si on arrive ici, quelque chose s'est mal passé

def generer_ecriture_paiement_client(transaction: FinancialTransaction, session: Session = db.session):
    """
    Génère et enregistre une EcritureComptable pour le règlement d'une transaction client ('Entrée').
    Débit Banque (51) / Crédit Client (410).

    Args:
        transaction: L'objet Transaction ('Entrée') qui vient d'être marquée comme 'Réglée'.
        session: La session SQLAlchemy à utiliser.

    Returns:
        EcritureComptable: L'écriture de paiement créée, ou None en cas d'erreur ou si déjà générée.
    """
    logger.info(f"Tentative de génération d'écriture de paiement pour Transaction ID: {transaction.id}")

    if not isinstance(transaction, Revenue) or transaction.reglement != 'Réglée':
        logger.warning(f"Conditions non remplies pour générer l'écriture de paiement pour Transaction ID: {transaction.id} (Type: {transaction.trans_type}, Règlement: {transaction.reglement})")
        return None

    organisation_id = transaction.organisation_id
    montant = transaction.montant
    # Utiliser la date du jour pour le paiement, ou la date de la transaction ?
    # Pour l'instant, utilisons la date du jour comme date d'écriture du paiement.
    date_paiement = date.today() # Ou transaction.date si tu préfères
    description_origine = transaction.description
    exercice_id = transaction.exercice_id # Le paiement doit être dans le même exercice ? A vérifier.

    # Créer une référence unique pour l'écriture de paiement pour éviter les doublons
    ref_paiement = f"Transaction:{transaction.id}:Paiement"

    # --- Vérifier si une écriture de paiement existe déjà ---
    ecriture_existante = session.query(EcritureComptable).filter_by(
        reference_origine=ref_paiement,
        organisation_id=organisation_id
    ).first()

    if ecriture_existante:
        logger.warning(f"Une écriture de paiement ({ref_paiement}) existe déjà pour Transaction ID: {transaction.id}. Aucune nouvelle écriture générée.")
        return ecriture_existante # Retourner l'existante pour ne pas bloquer le processus

    try:
        # Trouver les comptes Banque et Client par défaut
        compte_banque = session.query(CompteComptable).filter_by(
            organisation_id=organisation_id,
            numero=COMPTE_BANQUE_DEFAUT
        ).first()
        compte_client = session.query(CompteComptable).filter_by(
            organisation_id=organisation_id,
            numero=COMPTE_CLIENT_DEFAUT
        ).first()

        if not compte_banque:
            logger.error(f"Compte Banque par défaut '{COMPTE_BANQUE_DEFAUT}' non trouvé pour Organisation ID {organisation_id}.")
            return None
        if not compte_client:
            logger.error(f"Compte Client par défaut '{COMPTE_CLIENT_DEFAUT}' non trouvé pour Organisation ID {organisation_id}.")
            return None

        # --- Création de l'écriture et des lignes ---
        libelle_ecriture = f"Paiement Facture: {description_origine}"

        nouvelle_ecriture_paiement = EcritureComptable(
            date_ecriture=date_paiement,
            libelle=libelle_ecriture[:255],
            reference_origine=ref_paiement, # Utiliser la référence spécifique au paiement
            organisation_id=organisation_id,
            exercice_id=exercice_id
        )

        # Ligne de débit (Banque)
        ligne_debit = LigneEcriture(
            montant_debit=montant,
            montant_credit=0.0,
            compte_id=compte_banque.id,
            ecriture=nouvelle_ecriture_paiement
        )

        # Ligne de crédit (Client)
        ligne_credit = LigneEcriture(
            montant_debit=0.0,
            montant_credit=montant,
            compte_id=compte_client.id,
            ecriture=nouvelle_ecriture_paiement
        )

        session.add(nouvelle_ecriture_paiement)
        # Le commit sera fait dans le contrôleur

        logger.info(f"EcritureComptable de paiement (pré-commit): {nouvelle_ecriture_paiement} générée pour Transaction ID: {transaction.id}")
        return nouvelle_ecriture_paiement

    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération de l'écriture de paiement pour Transaction ID {transaction.id}: {e}", exc_info=True)
        return None
    

def creer_compte_pour_client(client: Client, session: Session = db.session):
    """
    Crée un compte comptable de type 411 pour un nouveau client.
    Trouve le prochain numéro disponible (ex: 411001, 411002...).

    Args:
        client: L'objet Client (déjà ajouté à la session mais pas encore commité).
        session: La session SQLAlchemy.

    Returns:
        CompteComptable: Le nouveau compte créé, ou None en cas d'erreur.
    """
    if not client or not client.organisation_id:
        logger.error("Client ou organisation_id manquant pour la création du compte comptable.")
        return None

    organisation_id = client.organisation_id
    prefixe_compte_client = "411" # Préfixe standard pour les comptes clients

    try:
        # Trouver le numéro de compte le plus élevé commençant par le préfixe pour cette organisation
        dernier_numero = session.query(func.max(CompteComptable.numero))\
            .filter(
                CompteComptable.organisation_id == organisation_id,
                CompteComptable.numero.like(f"{prefixe_compte_client}%")
            ).scalar() # scalar() retourne la première colonne de la première ligne, ou None

        prochain_numero_int = 1 # Commencer à 1 si aucun compte client n'existe
        if dernier_numero and dernier_numero.startswith(prefixe_compte_client):
            try:
                # Extraire la partie numérique après le préfixe et incrémenter
                partie_numerique = int(dernier_numero[len(prefixe_compte_client):])
                prochain_numero_int = partie_numerique + 1
            except ValueError:
                # Si la fin n'est pas un nombre, logguer une erreur et utiliser 1 (ou une autre logique)
                logger.warning(f"Impossible d'extraire le numéro de séquence depuis '{dernier_numero}'. Utilisation de 1.")
                prochain_numero_int = 1 # Ou gérer autrement

        # Formater le nouveau numéro (ex: 411001) - Ajuster le padding si besoin
        nouveau_numero = f"{prefixe_compte_client}{prochain_numero_int:03d}" # Pad avec des zéros jusqu'à 3 chiffres après 411

        # Vérifier si ce numéro existe déjà (sécurité en cas de concurrence, peu probable ici)
        compte_existant = session.query(CompteComptable).filter_by(
            organisation_id=organisation_id,
            numero=nouveau_numero
        ).first()
        if compte_existant:
             logger.error(f"Le numéro de compte client '{nouveau_numero}' existe déjà pour l'organisation {organisation_id}.")
             # Que faire ? Essayer le numéro suivant ? Pour l'instant, on retourne None.
             return None

        # Créer le nouveau compte comptable
        nouveau_compte = CompteComptable(
            numero=nouveau_numero,
            nom=f"Client - {client.nom}"[:100], # Utiliser le nom du client, tronqué si besoin
            type=ClasseCompte.CLASSE_4, # Type Tiers/Client
            description=f"Compte client pour {client.nom} (ID: {client.id})",
            solde_initial=0.0, # Solde initial toujours 0 pour un nouveau client
            actif=True,
            organisation_id=organisation_id
        )
        session.add(nouveau_compte)
        # Flush pour obtenir l'ID du compte si nécessaire avant le commit final
        session.flush()
        logger.info(f"Compte comptable '{nouveau_numero}' (pré-commit ID: {nouveau_compte.id}) créé pour Client ID {client.id}.")
        return nouveau_compte

    except Exception as e:
        logger.error(f"Erreur lors de la création du compte comptable pour Client ID {client.id}: {e}", exc_info=True)
        # Ne pas faire de rollback ici, la fonction appelante s'en chargera
        return None