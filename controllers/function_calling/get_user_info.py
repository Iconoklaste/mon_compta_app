from controllers.db_manager import db
from sqlalchemy import inspect
from models import User, Organisation
from flask_login import login_user, logout_user, login_required, current_user
import json


def get_user_info():
    """Récupère les informations de base de l'utilisateur actuel (nom, ville, etc.)."""
    user_data = {}
    if current_user and current_user.is_authenticated:
        mapper = inspect(User)
        
        for column in mapper.column_attrs:
            # column.key est le nom de l'attribut dans votre classe Python
            # getattr(current_user, column.key) récupère la valeur de cet attribut
            # On exclut le mot de passe par sécurité
            if column.key != 'password_hash': 
                 user_data[column.key] = getattr(current_user, column.key, None)
        
        if hasattr(current_user, 'organisation') and current_user.organisation:
            user_data['organisation_designation'] = current_user.organisation.designation
        else:
            user_data['organisation_designation'] = 'Organisation inconnue'
    else:
        # Gérer le cas où l'utilisateur n'est pas connecté
        user_data = {"error": "Utilisateur non connecté"}
    
    return json.dumps(user_data, ensure_ascii=False, default=str)