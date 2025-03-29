# c:\wamp\www\mon_compta_app\controllers\compta_controller.py

from flask import Blueprint, render_template, url_for, redirect, session
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client, User, Transaction, Projet  # Import Projet model
from datetime import datetime, timedelta
from sqlalchemy import func

compta_bp = Blueprint('compta', __name__, url_prefix='/compta')

@compta_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('users.logout'))

    # Get the user's organization
    organisation = user.organisation

    # --- Financial Summary ---
    # Calculate overall balance (total paid - total due) for the user's organization
    total_paid = db.session.query(func.sum(Transaction.montant)).filter(
        Transaction.type == 'Entrée',
        Transaction.organisation_id == organisation.id  # Filter by organization
    ).scalar() or 0
    total_due = db.session.query(func.sum(Transaction.montant)).filter(
        Transaction.type == 'Sortie',
        Transaction.organisation_id == organisation.id  # Filter by organization
    ).scalar() or 0
    overall_balance = total_paid - total_due

    # Calculate pending invoices (total amount of unpaid invoices) for the user's organization
    pending_invoices = db.session.query(func.sum(Transaction.montant)).filter(
        Transaction.type == 'Entrée',
        Transaction.reglement != 'Réglée',
        Transaction.organisation_id == organisation.id  # Filter by organization
    ).scalar() or 0

    # Calculate received payments (total amount of payments received) for the user's organization
    received_payments = db.session.query(func.sum(Transaction.montant)).filter(
        Transaction.type == 'Entrée',
        Transaction.reglement == 'Réglée',
        Transaction.organisation_id == organisation.id  # Filter by organization
    ).scalar() or 0

    # --- Projects to be billed ---
    # Calculate the total amount remaining to be billed for ongoing projects
    remaining_to_bill_projects = 0
    ongoing_projects = Projet.query.filter_by(statut="En cours", organisation_id=organisation.id).all()
    for project in ongoing_projects:
        total_billed = sum(transaction.montant for transaction in project.transactions)
        remaining_to_bill_projects += project.prix_total - total_billed



    # --- Recent Transactions ---
    # Get the 10 most recent transactions for the user's organization
    recent_transactions = Transaction.query.filter(Transaction.organisation_id == organisation.id).order_by(Transaction.date.desc()).limit(10).all()

    # --- Alerts and Reminders ---
    # Find overdue invoices for the user's organization
    today = datetime.now()
    overdue_invoices = []
    for transaction in Transaction.query.filter(
            Transaction.type == 'Sortie',
            Transaction.reglement != 'Réglée',
            Transaction.organisation_id == organisation.id # Filter by organization
    ).all():
        if transaction.due_date and transaction.due_date < today:
            days_overdue = (today - transaction.due_date).days
            # Access the client through the projet
            overdue_invoices.append({'id': transaction.id, 'client': transaction.projet.client, 'days_overdue': days_overdue})

    # Find clients with negative balances for the user's organization
    negative_balance_clients = []
    for client in Client.query.all():
        # Calculate total paid and due for each client using subqueries
        client_total_paid = db.session.query(func.sum(Transaction.montant)).filter(
            Transaction.type == 'Entrée',
            Transaction.projet.has(Projet.client_id == client.id),
            Transaction.organisation_id == organisation.id # Filter by organization
        ).scalar() or 0
        client_total_due = db.session.query(func.sum(Transaction.montant)).filter(
            Transaction.type == 'Sortie',
            Transaction.projet.has(Projet.client_id == client.id),
            Transaction.organisation_id == organisation.id # Filter by organization
        ).scalar() or 0
        client_balance = client_total_paid - client_total_due
        if client_balance < 0:
            negative_balance_clients.append({'nom': client.nom, 'balance': client_balance})

    return render_template(
        'compta/compta_index.html',
        overall_balance=overall_balance,
        pending_invoices=pending_invoices,
        received_payments=received_payments,
        recent_transactions=recent_transactions,
        overdue_invoices=overdue_invoices,
        negative_balance_clients=negative_balance_clients,
        remaining_to_bill_projects=remaining_to_bill_projects
    )
