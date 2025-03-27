# c:\wamp\www\mon_compta_app\controllers\clients_controller.py

from flask import Blueprint, request, jsonify
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/ajouter_client', methods=['POST'])
@login_required
def ajouter_client():
    data = request.get_json()
    nom = data.get('nom')
    adresse = data.get('adresse')
    code_postal = data.get('code_postal')
    ville = data.get('ville')
    telephone = data.get('telephone')
    mail = data.get('mail')

    if nom:
        new_client = Client(nom=nom, adresse=adresse, code_postal=code_postal, ville=ville, telephone=telephone, mail=mail)
        db.session.add(new_client)
        db.session.commit()
        return jsonify({'success': True, 'client_id': new_client.id})
    return jsonify({'success': False})
