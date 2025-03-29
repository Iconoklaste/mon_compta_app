# c:\wamp\www\mon_compta_app\controllers\clients_controller.py

from flask import Blueprint, request, jsonify, render_template
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client, Projet, Transaction

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/')  # Add this route
@login_required
def clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

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

@clients_bp.route('/<int:client_id>')
@login_required
def client_dashboard(client_id):
    client = Client.query.get_or_404(client_id)
    projets = client.projets  # Liste des projets du client
    transactions = [t for projet in projets for t in projet.transactions]  # Toutes les transactions liées

    total_paye = sum(t.montant for t in transactions if t.type == "paiement")
    total_du = sum(t.montant for t in transactions if t.type == "facture")

    return render_template(
        'client_dashboard.html',
        client=client,
        projets=projets,
        transactions=transactions,
        total_paye=total_paye,
        total_du=total_du,
        solde=total_paye - total_du
    )
