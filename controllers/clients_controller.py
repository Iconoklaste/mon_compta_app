# c:\wamp\www\mon_compta_app\controllers\clients_controller.py

from flask import Blueprint, request, jsonify, render_template, flash
from flask_wtf.csrf import validate_csrf
from sqlalchemy.exc import IntegrityError, DataError
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client, Projet, Transaction
from forms.forms import ClientForm
import itertools
import json

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/')
@login_required
def clients():
    """Render the clients list page."""
    clients = Client.query.all()
    return render_template('clients.html',
                           clients=clients,
                           current_page='CRM')

@clients_bp.route('/ajouter_client', methods=['POST'])
@login_required
def ajouter_client():
    """Add a new client."""
    try:
        validate_csrf(request.headers.get('X-CSRFToken'))
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erreur CSRF'}), 400

    # Get the JSON data from the request body
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No JSON data provided'}), 400

    # Create the form with the JSON data
    form = ClientForm(data=data)

    if form.validate():
        try:
            new_client = Client(
                nom=form.nom.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail=form.mail.data
            )
            db.session.add(new_client)
            db.session.commit()
            return jsonify({'success': True, 'client_id': new_client.id})
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Erreur de contrainte d\'intégrité (doublon, etc.)'}), 500
        except DataError as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Erreur de données (format incorrect, etc.)'}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        errors = {field: errors for field, errors in form.errors.items()}
        return jsonify({'success': False, 'errors': errors, 'message': 'Erreur de validation'}), 400

@clients_bp.route('/<int:client_id>')
@login_required
def client_dashboard(client_id):
    """Render the client dashboard."""
    client = Client.query.get_or_404(client_id)
    projets = client.projets
    transactions = list(itertools.chain.from_iterable(projet.transactions for projet in projets))

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
