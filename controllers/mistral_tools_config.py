# Importez les fonctions réelles
from controllers.function_calling.get_user_info import get_user_info
from controllers.function_calling.func_project import get_project_details_by_name, get_project_id_for_display
# from controllers.function_calling.autre_fonction import autre_fonction

# Description des outils
TOOLS_LIST = [
    ## TOOLS CONCERANT L'USER
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Récupère les informations de base sur l'utilisateur actuellement connécté",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    ## TOOLS CONCERNANT LES PROJET
    {
        "type": "function",
        "function": {
            "name": "get_project_details_by_name",
            "description": "Récupère les détails complets d'un projet spécifique en se basant sur son nom. À utiliser lorsque l'utilisateur demande des informations ou le statut d'un projet, pour pouvoir les résumer dans la conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom_projet": {
                        "type": "string",
                        "description": "Le nom exact du projet à rechercher."
                    }
                },
                "required": ["nom_projet"] # Le nom du projet est obligatoire
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_id_for_display",
            "description": "Recherche l'ID d'un projet par son nom afin de déclencher l'affichage de sa page de détail. À utiliser lorsque l'utilisateur demande explicitement d'afficher, de montrer ou d'ouvrir la page d'un projet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom_projet": {
                        "type": "string",
                        "description": "Le nom (approximatif ou exact) du projet dont il faut afficher la page."
                    }
                },
                "required": ["nom_projet"]
            }
        }
    },

    # {
    #     "type": "function",
    #     "function": {
    #         "name": "autre_fonction",
    #         "description": "Description de l'autre fonction...",
    #         "parameters": { ... } # Définir les paramètres si nécessaire
    #     }
    # },
]

# Dictionnaire des fonctions disponibles
AVAILABLE_FUNCTIONS = {
    "get_user_info": get_user_info,
    "get_project_details_by_name": get_project_details_by_name,
    "get_project_id_for_display": get_project_id_for_display,
    # "autre_fonction": autre_fonction,
}
