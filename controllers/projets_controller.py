from flask import Blueprint, render_template, redirect, session, url_for, request, abort, flash
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, Client, Transaction, Organisation, Projet, Phase, Jalon
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
    
    # Populate phases and jalons in the form
    form.phases.entries = []
    for phase in projet.phases:
        phase_form = form.phases.append_entry()
        phase_form.nom.data = phase.nom
        phase_form.date_debut.data = phase.date_debut
        phase_form.date_fin.data = phase.date_fin
        phase_form.statut.data = phase.statut

    form.jalons.entries = []
    for jalon in projet.jalons:
        jalon_form = form.jalons.append_entry()
        jalon_form.nom.data = jalon.nom
        jalon_form.date.data = jalon.date

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

        # Update phases
        for i, phase_form in enumerate(form.phases):
            if i < len(projet.phases):
                phase = projet.phases[i]
                phase.nom = phase_form.nom.data
                phase.date_debut = phase_form.date_debut.data
                phase.date_fin = phase_form.date_fin.data
                phase.statut = phase_form.statut.data
            else:
                phase = Phase(
                    nom=phase_form.nom.data,
                    date_debut=phase_form.date_debut.data,
                    date_fin=phase_form.date_fin.data,
                    statut=phase_form.statut.data,
                    projet_id=projet.id
                )
                db.session.add(phase)

        # Update jalons
        for i, jalon_form in enumerate(form.jalons):
            if i < len(projet.jalons):
                jalon = projet.jalons[i]
                jalon.nom = jalon_form.nom.data
                jalon.date = jalon_form.date.data
            else:
                jalon = Jalon(
                    nom=jalon_form.nom.data,
                    date=jalon_form.date.data,
                    projet_id=projet.id
                )
                db.session.add(jalon)

        db.session.commit()
        flash('Projet modifié avec succès!', 'success')
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
    avancement = calculer_avancement_projet(projet)
    return render_template('projet_detail.html',
                           projet=projet,
                           transactions=transactions,
                           remaining_to_bill=remaining_to_bill,
                           client=client,
                           avancement=avancement)

@projets_bp.route('/ajouter_projet', methods=['GET', 'POST'])
@login_required
def ajouter_projet():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        abort(404)
    form = ProjetForm()
    clients = Client.query.all()
    form.client_id.choices = [(client.id, client.nom) for client in clients]
    if form.validate_on_submit():
        projet = Projet(
            nom=form.nom.data,
            client_id=form.client_id.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            statut=form.statut.data,
            prix_total=form.prix_total.data,
            organisation_id=session['organisation_id'],
            user_id=session['user_id']
        )
        db.session.add(projet)
        db.session.commit()

        for phase_form in form.phases:
            phase = Phase(
                nom=phase_form.nom.data,
                date_debut=phase_form.date_debut.data,
                date_fin=phase_form.date_fin.data,
                statut=phase_form.statut.data,
                projet_id=projet.id
            )
            db.session.add(phase)

        for jalon_form in form.jalons:
            jalon = Jalon(
                nom=jalon_form.nom.data,
                date=jalon_form.date.data,
                projet_id=projet.id
            )
            db.session.add(jalon)

        db.session.commit()
        flash('Projet ajouté avec succès!', 'success')
        return redirect(url_for('projets.projets'))
    return render_template('ajouter_projet.html', form=form, title="Ajouter un projet")

def calculer_avancement_projet(projet):
    phases = projet.phases
    if not phases:
        return 0
    phases_terminees = sum(1 for phase in phases if phase.statut == "Terminée")
    return (phases_terminees / len(phases)) * 100
