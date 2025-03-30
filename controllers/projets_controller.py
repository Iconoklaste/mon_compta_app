from flask import Blueprint, render_template, redirect, session, url_for, request, abort
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, Client, Transaction, Organisation, Projet
from datetime import date
from forms.forms import ProjetForm

projets_bp = Blueprint('projets', __name__)

@projets_bp.route('/projets')
@login_required
def projets():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        abort(404)
    projets = Projet.query.filter_by(user_id=user_id).all()
    return render_template('projets.html', projets=projets)


@projets_bp.route('/projet/<int:projet_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    form = ProjetForm(obj=projet)

    if form.validate_on_submit():
        client = Client.query.get(form.client_id.data)
        if not client:
            abort(404)
        projet.nom = form.nom.data
        projet.client_id = form.client_id.data
        projet.date_debut = form.date_debut.data
        projet.date_fin = form.date_fin.data
        projet.statut = form.statut.data
        projet.prix_total = form.prix_total.data

        db.session.commit()
        return redirect(url_for('projets.projet_detail', projet_id=projet.id))
    else:
        return render_template('projet_edit.html', projet=projet, form=form)


@projets_bp.route('/projet/<int:projet_id>/supprimer', methods=['POST'])
@login_required
def supprimer_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    # Delete related transactions first (if necessary)
    for transaction in projet.transactions:
        db.session.delete(transaction)
    db.session.delete(projet)
    db.session.commit()
    return redirect(url_for('projets.projets'))

@projets_bp.route('/projet/<int:projet_id>')
@login_required
def projet_detail(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    transactions = Transaction.query.filter_by(projet_id=projet_id).all()
    total_billed = sum(transaction.montant for transaction in transactions)
    remaining_to_bill = projet.prix_total - total_billed
    client = projet.client
    return render_template('projet_detail.html',
                           projet=projet,
                           transactions=transactions,
                           remaining_to_bill=remaining_to_bill,
                           client=client)

@projets_bp.route('/ajouter_projet', methods=['GET', 'POST'])
@login_required
def ajouter_projet():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        abort(404)
    clients = Client.query.all()
    status_options = ["En attente", "En cours", "Terminé", "Annulé"]
    if request.method == 'POST':
        nom = request.form['nom']
        client_id = request.form['client_id']
        date_debut_str = request.form['date_debut']
        date_fin_str = request.form['date_fin']
        statut = request.form['statut']
        prix_total = int(request.form['prix_total']) if request.form['prix_total'] else 0
        date_debut = date.fromisoformat(date_debut_str) if date_debut_str else None
        date_fin = date.fromisoformat(date_fin_str) if date_fin_str else None
        organisation = Organisation.query.first()
        if not organisation:
            abort(404)

        client = Client.query.get(client_id)
        if not client:
            abort(404)

        nouveau_projet = Projet(nom=nom, date_debut=date_debut, date_fin=date_fin, statut=statut, prix_total=prix_total, organisation=organisation, user=user, client=client)
        db.session.add(nouveau_projet)
        db.session.commit()
        return redirect(url_for('projets.projets'))

    return render_template('ajouter_projet.html', clients=clients, status_options=status_options)
