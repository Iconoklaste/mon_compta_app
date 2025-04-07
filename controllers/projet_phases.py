# c:\wamp\www\mon_compta_app\controllers\projet_phases.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, session
from flask_wtf.csrf import validate_csrf
from controllers.db_manager import db
from models import Phase, Projet, Jalon
from forms.forms import PhaseForm, JalonForm
from controllers.users_controller import login_required
from datetime import date

projet_phases_bp = Blueprint('projet_phases', __name__, url_prefix='/projets/<int:projet_id>/phases')

@projet_phases_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_phase(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    form = PhaseForm()
    if form.validate_on_submit():
        phase = Phase(
            nom=form.nom.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            statut=form.statut.data,
            projet_id=projet_id
        )
        db.session.add(phase)
        db.session.flush()  # Get the phase ID

        # Add jalons
        for jalon_form in form.jalons:
            jalon = Jalon(
                nom=jalon_form.nom.data,
                date=jalon_form.date.data,
                phase_id=phase.id,
                projet_id=projet_id
            )
            db.session.add(jalon)

        db.session.commit()
        flash('Phase et jalons ajoutés avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    return render_template('phase_form.html', form=form, projet=projet, title="Ajouter une phase")

@projet_phases_bp.route('/<int:phase_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_phase(projet_id, phase_id):
    projet = Projet.query.get_or_404(projet_id)
    phase = Phase.query.get_or_404(phase_id)

    # Populate the form with existing jalons
    form = PhaseForm(obj=phase)

    if form.validate_on_submit():
        phase.nom = form.nom.data
        phase.date_debut = form.date_debut.data
        phase.date_fin = form.date_fin.data
        phase.statut = form.statut.data

        # Handle jalon deletion
        existing_jalon_ids = {jalon.id for jalon in phase.jalons}
        submitted_jalon_ids = set()
        for jalon_form in form.jalons:
            if 'id' in jalon_form:
                submitted_jalon_ids.add(int(jalon_form['id']))
        jalons_to_delete = existing_jalon_ids - submitted_jalon_ids

        for jalon_id in jalons_to_delete:
            jalon = Jalon.query.get(jalon_id)
            if jalon:
                db.session.delete(jalon)

        # Handle jalon modification and creation
        for jalon_form in form.jalons:
            if 'id' in jalon_form:
                jalon_id = int(jalon_form['id'])
                jalon = Jalon.query.get(jalon_id)
                if jalon:
                    jalon.nom = jalon_form.nom.data
                    jalon.date = jalon_form.date.data
                    jalon.atteint = jalon_form.atteint.data
            else:
                # New jalon
                new_jalon = Jalon(
                    nom=jalon_form.nom.data,
                    date=jalon_form.date.data,
                    atteint = jalon_form.atteint.data,
                    phase_id=phase_id,
                    projet_id=projet_id
                )
                db.session.add(new_jalon)

        db.session.commit()
        flash('Phase modifiée avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))

    return render_template('phase_form.html', form=form, projet=projet, title="Modifier une phase", projet_id=projet_id, phase_id=phase_id)

@projet_phases_bp.route('/<int:phase_id>/supprimer', methods=['POST'])
@login_required
def supprimer_phase(projet_id, phase_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash("Erreur CSRF", 'danger')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    phase = Phase.query.get_or_404(phase_id)
    db.session.delete(phase)
    db.session.commit()
    flash('Phase supprimée avec succès!', 'success')
    return redirect(url_for('projets.projet_detail', projet_id=projet_id))
