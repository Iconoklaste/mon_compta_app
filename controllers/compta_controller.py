# c:\wamp\www\mon_compta_app\controllers\compta_controller.py

from flask import Blueprint, render_template, url_for, redirect, session, flash
from controllers.db_manager import db
from controllers.users_controller import login_required
from reports.report_generators import (generate_balance_sheet, 
                                       generate_income_statement, 
                                       generate_general_ledger,
                                       generate_cash_flow)
from models import Client, User, Transaction, Projet, ExerciceComptable   # Import Projet model
from datetime import datetime, timedelta, date
from sqlalchemy import func
import logging

compta_bp = Blueprint('compta', __name__, url_prefix='/compta')
logger = logging.getLogger(__name__)

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
        current_page='Comptabilité',
        overall_balance=overall_balance,
        pending_invoices=pending_invoices,
        received_payments=received_payments,
        recent_transactions=recent_transactions,
        overdue_invoices=overdue_invoices,
        negative_balance_clients=negative_balance_clients,
        remaining_to_bill_projects=remaining_to_bill_projects
    )
@compta_bp.route('/bilan') # Si dans compta_controller
@login_required
def afficher_bilan():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        flash("Utilisateur ou organisation non trouvé.", "warning")
        return redirect(url_for('users.index')) # Ou une autre page

    organisation_id = user.organisation_id
    # Pour le test, on prend la date du jour. Plus tard, on pourra ajouter un sélecteur de date.
    date_fin_bilan = date.today()

    try:
        bilan_data = generate_balance_sheet(organisation_id, date_fin_bilan)

        # Vérifier l'équilibre et afficher un message si besoin
        if not bilan_data['equilibre']:
             desequilibre_val = bilan_data.get('desequilibre', 0.0)
             logger.warning(f"Bilan déséquilibré pour Org ID {organisation_id} à la date {date_fin_bilan}. Différence: {desequilibre_val:.2f}")
             flash(f"Attention : Le bilan calculé est déséquilibré (différence de {desequilibre_val:.2f} €). Vérifiez les écritures.", "danger")

        return render_template('compta/reports/bilan.html', # Chemin vers le nouveau template
                               bilan=bilan_data,
                               current_page='Bilan Comptable')

    except ValueError as ve:
        logger.error(f"Erreur lors de la génération du bilan (ValueError): {ve}", exc_info=True)
        flash(f"Erreur de données lors de la génération du bilan : {ve}", "danger")
        return redirect(url_for('compta.index')) # Rediriger vers le tableau de bord compta
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération du bilan: {e}", exc_info=True)
        flash("Une erreur inattendue est survenue lors de la génération du bilan.", "danger")
        return redirect(url_for('compta.index')) # Rediriger vers le tableau de bord compta
    

@compta_bp.route('/compte-resultat') # Nouvelle route
@login_required
def afficher_compte_resultat():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        flash("Utilisateur ou organisation non trouvé.", "warning")
        return redirect(url_for('users.index'))

    organisation_id = user.organisation_id
    today = date.today()

    # --- Déterminer la période (Exemple: exercice comptable courant) ---
    # Recherche de l'exercice contenant la date d'aujourd'hui
    exercice_courant = db.session.query(ExerciceComptable).filter(
        ExerciceComptable.organisation_id == organisation_id,
        ExerciceComptable.date_debut <= today,
        ExerciceComptable.date_fin >= today
        # Optionnel: Ajouter filtre sur statut 'Ouvert' si pertinent
        # ExerciceComptable.statut == "Ouvert"
    ).order_by(ExerciceComptable.date_debut.desc()).first()

    if exercice_courant:
        date_debut_periode = exercice_courant.date_debut
        # Pour le compte de résultat, on prend souvent la période complète de l'exercice
        date_fin_periode = exercice_courant.date_fin
        # Alternative: prendre jusqu'à aujourd'hui: date_fin_periode = today
    else:
        # Fallback: si aucun exercice courant, prendre l'année civile en cours ?
        # Ou afficher une erreur ? Pour l'instant, année civile.
        logger.warning(f"Aucun exercice comptable courant trouvé pour Org ID {organisation_id} à la date {today}. Utilisation de l'année civile.")
        date_debut_periode = date(today.year, 1, 1)
        date_fin_periode = date(today.year, 12, 31)
        # Ou afficher une erreur et rediriger :
        # flash("Impossible de déterminer l'exercice comptable courant.", "warning")
        # return redirect(url_for('compta.index'))

    try:
        # Appeler la fonction de génération
        compte_resultat_data = generate_income_statement(
            organisation_id,
            date_debut_periode,
            date_fin_periode
        )

        return render_template('compta/reports/compte_resultat.html', # Chemin vers le nouveau template
                               compte_resultat=compte_resultat_data,
                               current_page='Compte de Résultat')

    except ValueError as ve:
        logger.error(f"Erreur lors de la génération du compte de résultat (ValueError): {ve}", exc_info=True)
        flash(f"Erreur de données lors de la génération du compte de résultat : {ve}", "danger")
        return redirect(url_for('compta.index'))
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération du compte de résultat: {e}", exc_info=True)
        flash("Une erreur inattendue est survenue lors de la génération du compte de résultat.", "danger")
        return redirect(url_for('compta.index'))
    
@compta_bp.route('/grand-livre') # Nouvelle route
@login_required
def afficher_grand_livre():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        flash("Utilisateur ou organisation non trouvé.", "warning")
        return redirect(url_for('users.index'))

    organisation_id = user.organisation_id
    today = date.today()

    # --- Déterminer la période (Exemple: exercice comptable courant) ---
    # (Même logique que pour le compte de résultat)
    exercice_courant = db.session.query(ExerciceComptable).filter(
        ExerciceComptable.organisation_id == organisation_id,
        ExerciceComptable.date_debut <= today,
        ExerciceComptable.date_fin >= today
    ).order_by(ExerciceComptable.date_debut.desc()).first()

    if exercice_courant:
        date_debut_periode = exercice_courant.date_debut
        date_fin_periode = exercice_courant.date_fin
        # Alternative: prendre jusqu'à aujourd'hui: date_fin_periode = today
    else:
        logger.warning(f"Aucun exercice comptable courant trouvé pour Org ID {organisation_id} à la date {today}. Utilisation de l'année civile.")
        date_debut_periode = date(today.year, 1, 1)
        date_fin_periode = date(today.year, 12, 31)
        # Ou afficher une erreur et rediriger
        # flash("Impossible de déterminer l'exercice comptable courant.", "warning")
        # return redirect(url_for('compta.index'))

    try:
        # Appeler la fonction de génération du grand livre
        grand_livre_data = generate_general_ledger(
            organisation_id,
            date_debut_periode,
            date_fin_periode
        )

        return render_template('compta/reports/grand_livre.html', # Chemin vers le nouveau template
                               grand_livre=grand_livre_data,
                               current_page='Grand Livre')

    except ValueError as ve:
        logger.error(f"Erreur lors de la génération du grand livre (ValueError): {ve}", exc_info=True)
        flash(f"Erreur de données lors de la génération du grand livre : {ve}", "danger")
        return redirect(url_for('compta.index'))
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération du grand livre: {e}", exc_info=True)
        flash("Une erreur inattendue est survenue lors de la génération du grand livre.", "danger")
        return redirect(url_for('compta.index'))
    
@compta_bp.route('/flux-tresorerie') # Nouvelle route
@login_required
def afficher_flux_tresorerie():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        flash("Utilisateur ou organisation non trouvé.", "warning")
        return redirect(url_for('users.index'))

    organisation_id = user.organisation_id
    today = date.today()

    # --- Déterminer la période (Exemple: exercice comptable courant) ---
    # (Même logique que pour le compte de résultat et grand livre)
    exercice_courant = db.session.query(ExerciceComptable).filter(
        ExerciceComptable.organisation_id == organisation_id,
        ExerciceComptable.date_debut <= today,
        ExerciceComptable.date_fin >= today
    ).order_by(ExerciceComptable.date_debut.desc()).first()

    if exercice_courant:
        date_debut_periode = exercice_courant.date_debut
        date_fin_periode = exercice_courant.date_fin
        # Alternative: prendre jusqu'à aujourd'hui: date_fin_periode = today
    else:
        logger.warning(f"Aucun exercice comptable courant trouvé pour Org ID {organisation_id} à la date {today}. Utilisation de l'année civile.")
        date_debut_periode = date(today.year, 1, 1)
        date_fin_periode = date(today.year, 12, 31)
        # Ou afficher une erreur et rediriger
        # flash("Impossible de déterminer l'exercice comptable courant.", "warning")
        # return redirect(url_for('compta.index'))

    try:
        # Appeler la fonction de génération du flux de trésorerie
        flux_tresorerie_data = generate_cash_flow(
            organisation_id,
            date_debut_periode,
            date_fin_periode
        )

        # Vérifier si le calcul est cohérent
        if not flux_tresorerie_data['is_verified']:
            diff = flux_tresorerie_data['verification_difference']
            logger.warning(f"Flux de trésorerie incohérent pour Org ID {organisation_id} "
                           f"({date_debut_periode} à {date_fin_periode}). Différence: {diff:.2f} €")
            flash(f"Attention : Incohérence détectée dans le calcul du flux de trésorerie "
                  f"(différence de {diff:.2f} € entre le calcul par flux et le solde direct). "
                  f"Certains flux pourraient être mal classifiés ou des écritures manquantes/erronées.", "warning")

        return render_template('compta/reports/flux_tresorerie.html', # Chemin vers le nouveau template
                               flux_tresorerie=flux_tresorerie_data,
                               current_page='Flux de Trésorerie')

    except ValueError as ve:
        logger.error(f"Erreur lors de la génération du flux de trésorerie (ValueError): {ve}", exc_info=True)
        flash(f"Erreur de données lors de la génération du flux de trésorerie : {ve}", "danger")
        return redirect(url_for('compta.index'))
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la génération du flux de trésorerie: {e}", exc_info=True)
        flash("Une erreur inattendue est survenue lors de la génération du flux de trésorerie.", "danger")
        return redirect(url_for('compta.index'))