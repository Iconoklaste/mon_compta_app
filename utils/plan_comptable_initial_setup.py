# utils/comptabilite_utils.py

import json
import os
import logging
from typing import List, Optional, Dict, Any, Set

from sqlalchemy.exc import SQLAlchemyError

# Assure-toi que les chemins d'import sont corrects par rapport à la structure de ton projet
# Si 'utils' est au même niveau que 'models', l'import devrait fonctionner.
# Sinon, ajuste le chemin (ex: from ..models import CompteComptable, Organisation, ClasseCompte)
try:
    # Importe les modèles depuis le package 'models'
    from models import Organisation # Organisation est dans models/organisations.py
    # Importe CompteComptable ET ClasseCompte depuis models/compte_comptable.py
    from models.compte_comptable import CompteComptable, ClasseCompte
    # Importe la session db
    from controllers.db_manager import db
except ImportError as e:
    print(f"Avertissement: Impossible d'importer les modèles/db. Erreur: {e}. Vérifie les chemins.")
    # ... reste du bloc except ...
    pass

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)

# --- Mapping des formes juridiques aux scénarios de sélection ---
# Scénario 1: Minimaliste ('condensed' uniquement)
SCENARIO_MINIMALISTE_FORMES = {'Entreprise Individuelle', 'Association', 'Autre'}
# Scénario 2: Généraliste ('condensed' et 'base')
SCENARIO_GENERALISTE_FORMES = {'SARL', 'EURL', 'SAS', 'SA', 'SASU'}

# --- Mapping des numéros de classe JSON vers l'Enum ClasseCompte ---
# Cela évite de devoir parser la chaîne de l'enum à chaque fois
CLASSE_NUMERO_TO_ENUM: Dict[int, ClasseCompte] = {
    1: ClasseCompte.CLASSE_1,
    2: ClasseCompte.CLASSE_2,
    3: ClasseCompte.CLASSE_3,
    4: ClasseCompte.CLASSE_4,
    5: ClasseCompte.CLASSE_5,
    6: ClasseCompte.CLASSE_6,
    7: ClasseCompte.CLASSE_7,
    8: ClasseCompte.CLASSE_8,
}

def get_pcg_file_path() -> str:
    """
    Récupère le chemin du fichier PCG depuis la variable d'environnement
    ou retourne le chemin par défaut.
    """
    # TODO -> A ajouter dans l'interface d'administration :
    # Permettre à un admin de définir/modifier ce chemin via l'interface,
    # potentiellement en le stockant dans une table de configuration globale.
    default_path = os.path.join('static', 'asset', 'pcg-24-raw.json')
    # Pour l'instant, on suppose qu'il est exécuté depuis la racine du projet Flask.
    return os.getenv('PCG_FILE_PATH', default_path)


def _determine_allowed_systems(forme_juridique: Optional[str]) -> Set[str]:
    """
    Détermine les clés 'system' autorisées en fonction de la forme juridique.
    """
    if forme_juridique in SCENARIO_GENERALISTE_FORMES:
        # Scénario Généraliste: 'condensed' et 'base'
        return {'condensed', 'base'}
    elif forme_juridique in SCENARIO_MINIMALISTE_FORMES:
        # Scénario Minimaliste: 'condensed' uniquement
        return {'condensed'}
    else:
        # Cas par défaut ou forme juridique non reconnue : on prend le minimaliste
        logger.warning(f"Forme juridique '{forme_juridique}' non explicitement mappée. Utilisation du scénario minimaliste.")
        return {'condensed'}

def _process_accounts_recursive(
    accounts_data: List[Dict[str, Any]],
    classe_enum: ClasseCompte,
    allowed_systems: Set[str],
    organisation_id: int
) -> List[CompteComptable]:
    """
    Fonction récursive pour traiter une liste de comptes et leurs enfants.
    """
    created_accounts: List[CompteComptable] = []
    if not accounts_data:
        return created_accounts

    for account_data in accounts_data:
        account_system = account_data.get("system")
        account_number = account_data.get("number")
        account_label = account_data.get("label")

        # Vérifie si le compte correspond aux critères de sélection
        if account_system in allowed_systems and account_number and account_label:
            # Crée l'objet CompteComptable
            # Note: On utilise les valeurs par défaut du modèle pour solde_initial et actif
            compte = CompteComptable(
                numero=str(account_number), # Assure que le numéro est une chaîne
                nom=account_label,
                type=classe_enum, # L'enum déterminé par la classe parente
                organisation_id=organisation_id,
                description=f"Compte généré automatiquement depuis PCG ({account_system})", # Optionnel
                # solde_initial=0.0, # Déjà par défaut dans le modèle
                # actif=True         # Déjà par défaut dans le modèle
            )
            created_accounts.append(compte)

        # Traite les sous-comptes récursivement (s'ils existent)
        if "accounts" in account_data:
            created_accounts.extend(
                _process_accounts_recursive(
                    account_data["accounts"],
                    classe_enum, # Les sous-comptes héritent de la classe du parent direct dans cette structure
                    allowed_systems,
                    organisation_id
                )
            )
    return created_accounts

def generate_default_plan_comptable(organisation: Organisation) -> Optional[List[CompteComptable]]:
    """
    Génère un plan comptable par défaut pour une organisation donnée
    en se basant sur un fichier JSON PCG et la forme juridique de l'organisation.

    Args:
        organisation: L'objet Organisation pour laquelle générer le plan.

    Returns:
        La liste des objets CompteComptable créés et ajoutés à la session,
        ou None en cas d'erreur majeure (ex: fichier PCG introuvable).
    """
    if not organisation or not organisation.id:
        logger.error("Organisation invalide ou sans ID fournie.")
        return None

    pcg_path = get_pcg_file_path()
    logger.info(f"Tentative de génération du plan comptable pour l'organisation ID {organisation.id} ({organisation.designation}) "
                f"depuis le fichier : {pcg_path}")

    try:
        with open(pcg_path, 'r', encoding='utf-8') as f:
            pcg_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Erreur critique: Le fichier PCG '{pcg_path}' est introuvable.")
        # Tu pourrais lever une exception ici ou retourner None/liste vide
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Erreur critique: Impossible de parser le fichier JSON '{pcg_path}'. Erreur: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la lecture du fichier PCG '{pcg_path}': {e}")
        return None

    # Déterminer les systèmes de comptes à inclure
    allowed_systems = _determine_allowed_systems(organisation.forme_juridique)
    logger.info(f"Forme juridique: '{organisation.forme_juridique}'. Systèmes PCG sélectionnés: {allowed_systems}")

    all_new_comptes: List[CompteComptable] = []

    # Parcourir les classes du PCG
    for classe_data in pcg_data:
        classe_number = classe_data.get("number")
        classe_label = classe_data.get("label")
        classe_accounts = classe_data.get("accounts", [])

        if not isinstance(classe_number, int) or not classe_label:
            logger.warning(f"Ignoré: Entrée de classe invalide dans le JSON: {classe_data}")
            continue

        # Récupérer l'Enum ClasseCompte correspondant au numéro de classe
        classe_enum = CLASSE_NUMERO_TO_ENUM.get(classe_number)
        if not classe_enum:
            logger.warning(f"Ignoré: Numéro de classe '{classe_number}' non trouvé dans le mapping CLASSE_NUMERO_TO_ENUM.")
            continue

        logger.debug(f"Traitement de la {classe_enum.value}...")

        # Traiter les comptes de cette classe (et leurs enfants) récursivement
        comptes_de_classe = _process_accounts_recursive(
            classe_accounts,
            classe_enum,
            allowed_systems,
            organisation.id
        )
        all_new_comptes.extend(comptes_de_classe)

    if not all_new_comptes:
        logger.warning(f"Aucun compte comptable n'a été généré pour l'organisation ID {organisation.id}. "
                       f"Vérifiez le contenu du fichier PCG ('{pcg_path}') et les critères de sélection ({allowed_systems}).")
        return [] # Retourne une liste vide si aucun compte n'est généré

    # --- Insertion en base de données ---
    try:
        # Utilise la session db importée
        db.session.add_all(all_new_comptes)
        db.session.commit()
        logger.info(f"Succès: {len(all_new_comptes)} comptes comptables générés et enregistrés pour l'organisation ID {organisation.id}.")
        # Les objets dans all_new_comptes ont maintenant leur ID après le commit
        return all_new_comptes
    except SQLAlchemyError as e:
        db.session.rollback() # Important: annuler les changements en cas d'erreur
        logger.error(f"Erreur lors de l'enregistrement des comptes en base de données pour l'organisation ID {organisation.id}: {e}")
        # Tu pourrais vouloir relancer l'exception ou gérer l'erreur différemment
        return None # Indique qu'une erreur s'est produite
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur inattendue lors de l'enregistrement en base de données: {e}")
        return None

