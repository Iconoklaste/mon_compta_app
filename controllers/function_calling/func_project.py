import json
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask_login import current_user
from models import Projet, Client, User, Revenue, FinancialTransaction # Import necessary models
from controllers.db_manager import db

# Helper pour la sérialisation JSON (gère Decimal et date/datetime)
def json_serial(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, 'isoformat'): # Pour les dates/datetimes
         return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_project_details_by_name(nom_projet: str):
    """
    Récupère les détails d'un projet spécifique en fonction de son nom pour l'utilisateur actuel.
    Retourne les informations clés du projet au format JSON.
    """
    if not current_user or not current_user.is_authenticated:
        return json.dumps({"error": "Utilisateur non connecté"})

    organisation_id = current_user.organisation_id
    if not organisation_id:
         return json.dumps({"error": "Organisation de l'utilisateur non trouvée"})

    try:
        # Recherche du projet par nom exact et organisation
        # Utilisation de joinedload pour charger le client si nécessaire
        search_term = f"%{nom_projet}%"
        projets_trouves = db.session.query(Projet).options(joinedload(Projet.client)).filter(
            Projet.organisation_id == organisation_id,
            Projet.nom.ilike(search_term)
        ).order_by(Projet.nom).all()

        # --- Gérer les différents cas ---
        if not projets_trouves:
            # Aucun projet trouvé
            raise NoResultFound

        elif len(projets_trouves) == 1:
            # Un seul projet trouvé, on continue comme avant
            projet = projets_trouves[0]

            # --- Récupérer/Calculer les informations nécessaires (similaire à projet_detail) ---
            client_nom = projet.client.nom if projet.client else "N/A"

            # Calculs financiers (simplifiés pour l'exemple, peuvent être affinés)
            total_billed = db.session.query(func.sum(Revenue.montant)).filter(Revenue.projet_id == projet.id).scalar() or Decimal('0.0')
            total_paid = db.session.query(func.sum(Revenue.montant)).filter(
                Revenue.projet_id == projet.id,
                Revenue.reglement == 'Réglée'
            ).scalar() or Decimal('0.0')
            remaining_to_bill = (projet.prix_total or Decimal('0.0')) - total_billed
            due_balance = total_billed - total_paid

            # --- Construire le dictionnaire de sortie ---
            project_info = {
                "id": projet.id,
                "nom": projet.nom,
                "client_nom": client_nom,
                "statut": projet.statut,
                "date_debut": projet.date_debut, # Sera formaté par json_serial
                "date_fin": projet.date_fin,     # Sera formaté par json_serial
                "prix_total": projet.prix_total, # Sera formaté par json_serial
                "reste_a_facturer": remaining_to_bill, # Sera formaté par json_serial
                "solde_du": due_balance,             # Sera formaté par json_serial
                # Ajouter d'autres champs si pertinent pour le chatbot (description, progression...)
            }
            return json.dumps(project_info, default=json_serial, ensure_ascii=False)

        else:
            # Plusieurs projets trouvés
            matches = [{"id": p.id, "nom": p.nom} for p in projets_trouves]
            return json.dumps({
                "status": "multiple_matches",
                "message": f"J'ai trouvé {len(matches)} projets correspondant à '{nom_projet}'. Lequel voulez-vous consulter ?",
                "matches": matches
            }, ensure_ascii=False)


    except NoResultFound:
        return json.dumps({"error": f"Aucun projet nommé '{nom_projet}' trouvé pour votre organisation."})
    except Exception as e:
        # Log l'erreur e
        print(f"Erreur inattendue dans get_project_details_by_name: {e}") # Pour le debug
        return json.dumps({"error": "Une erreur interne est survenue lors de la recherche du projet."})

def get_project_id_for_display(nom_projet: str):
    """
    Recherche un projet par nom et retourne son ID pour déclencher l'affichage de sa page.
    Gère les cas où aucun ou plusieurs projets sont trouvés.
    """
    if not current_user or not current_user.is_authenticated:
        return json.dumps({"error": "Utilisateur non connecté"})
    organisation_id = current_user.organisation_id
    if not organisation_id:
         return json.dumps({"error": "Organisation de l'utilisateur non trouvée"})

    try:
        # Logique de recherche identique
        search_term = f"%{nom_projet}%"
        projets_trouves = db.session.query(Projet).filter(
            Projet.organisation_id == organisation_id,
            Projet.nom.ilike(search_term)
        ).order_by(Projet.nom).all()

        if not projets_trouves:
            raise NoResultFound

        elif len(projets_trouves) == 1:
            # Un seul projet trouvé -> statut pour redirection
            projet = projets_trouves[0]
            return json.dumps({
                "status": "redirect_needed", # Nouveau statut
                "id": projet.id,
                "nom": projet.nom
            }, ensure_ascii=False)

        else:
            # Plusieurs projets trouvés -> statut pour demander lequel afficher
            matches = [{"id": p.id, "nom": p.nom} for p in projets_trouves]
            return json.dumps({
                "status": "multiple_matches_for_redirect", # Nouveau statut
                "message": f"J'ai trouvé {len(matches)} projets correspondant à '{nom_projet}'. Quelle page de projet voulez-vous afficher ?",
                "matches": matches
            }, ensure_ascii=False)

    except NoResultFound:
        return json.dumps({"error": f"Aucun projet nommé '{nom_projet}' trouvé pour votre organisation."})
    except Exception as e:
        print(f"Erreur inattendue dans get_project_id_for_display: {e}")
        return json.dumps({"error": "Une erreur interne est survenue lors de la recherche de l'ID du projet."})