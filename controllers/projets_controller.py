from flask import Blueprint, render_template, redirect, session, url_for, request, abort, flash
from flask_wtf.csrf import validate_csrf
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, Client, Transaction, Organisation, Projet
from datetime import date
from forms.forms import ProjetForm, ClientForm

projets_bp = Blueprint('projets', __name__)

@projets_bp.route('/projets')
@login_required
def projets():
    user_id = session['user_id']
    projets = Projet.query.filter_by(user_id=user_id).all()
    return render_template('projets.html',
                           projets=projets,
                           current_page='Projets')


@projets_bp.route('/projet/<int:projet_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    form = ProjetForm(obj=projet)

    if form.validate_on_submit():
        projet.nom = form.nom.data
        projet.client_id = form.client_id.data
        projet.date_debut = form.date_debut.data
        projet.date_fin = form.date_fin.data
        projet.statut = form.statut.data
        projet.prix_total = form.prix_total.data

        db.session.commit()
        flash('Projet modifié avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet.id))
    return render_template('projet_edit.html', projet=projet, form=form)


@projets_bp.route('/projet/<int:projet_id>/supprimer', methods=['POST'])
@login_required
def supprimer_projet(projet_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        # Handle CSRF error (e.g., return an error response)
        return "CSRF token validation failed", 400
    projet = Projet.query.get_or_404(projet_id)
    # Delete related transactions first (if necessary)
    for transaction in projet.transactions:
        db.session.delete(transaction)
    db.session.delete(projet)
    db.session.commit()
    flash('Projet supprimé avec succès!', 'success')
    return redirect(url_for('projets.projets'))

@projets_bp.route('/<int:projet_id>')
@login_required
def projet_detail(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    client = Client.query.get_or_404(projet.client_id)
    transactions = Transaction.query.filter_by(projet_id=projet_id).all()

    # Recalculate phase progress
    for phase in projet.phases:
        total_jalons = len(phase.jalons)
        completed_jalons = sum(1 for j in phase.jalons if j.atteint)
        phase.progress = (completed_jalons / total_jalons) * 100 if total_jalons > 0 else 0

    # Recalculate overall project progress (example)
    total_phases = len(projet.phases)
    if total_phases > 0:
        projet.progress = sum(phase.progress for phase in projet.phases) / total_phases
    else:
        projet.progress = 0

    db.session.commit()

    # Calculate remaining to bill
    total_billed = db.session.query(func.sum(Transaction.montant)).filter(Transaction.projet_id == projet_id, Transaction.type == 'Facture').scalar() or 0
    total_paid = db.session.query(func.sum(Transaction.montant)).filter(Transaction.projet_id == projet_id, Transaction.type == 'Paiement').scalar() or 0
    remaining_to_bill = projet.prix_total - (total_billed - total_paid)

    return render_template('projet_detail.html', projet=projet, client=client, transactions=transactions, remaining_to_bill=remaining_to_bill)

@projets_bp.route('/ajouter_projet', methods=['GET', 'POST'])
@login_required
def ajouter_projet():
    form = ProjetForm()
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        abort(404)
    form.client_id.choices = [(client.id, client.nom) for client in Client.query.all()]
    form.statut.choices = [("En attente", "En attente"), ("En cours", "En cours"), ("Terminé", "Terminé"), ("Annulé", "Annulé")]

    if form.validate_on_submit():
        try:
            validate_csrf(form.csrf_token.data)
        except Exception as e:
            flash("Erreur CSRF", 'danger')
            return redirect(url_for('projets.ajouter_projet'))

        organisation = Organisation.query.first()
        if not organisation:
            flash("Aucune organisation trouvée.", 'danger')
            return redirect(url_for('projets.ajouter_projet'))

        client = Client.query.get(form.client_id.data)
        if not client:
            flash("Client non trouvé.", 'danger')
            return redirect(url_for('projets.ajouter_projet'))

        nouveau_projet = Projet(
            nom=form.nom.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            statut=form.statut.data,
            prix_total=form.prix_total.data,
            organisation=organisation,
            user=user,
            client=client
        )
        db.session.add(nouveau_projet)
        db.session.commit()
        flash('Projet ajouté avec succès!', 'success')
        return redirect(url_for('projets.projets'))

    return render_template('ajouter_projet.html', clients=Client.query.all(), form=form, status_options=["En attente", "En cours", "Terminé", "Annulé"])
