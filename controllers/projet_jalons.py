# c:\wamp\www\mon_compta_app\controllers\projet_jalons.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_wtf.csrf import validate_csrf
from controllers.db_manager import db
from models import Jalon, Projet, Phase
from forms.forms import JalonForm
from controllers.users_controller import login_required
from datetime import date
import logging

projet_jalons_bp = Blueprint('projet_jalons', __name__, url_prefix='/projets/<int:projet_id>/phases/<int:phase_id>/jalons')

@projet_jalons_bp.route('/<int:jalon_id>/update', methods=['POST'])
def update_jalon_status(projet_id, phase_id, jalon_id):
    jalon = Jalon.query.get_or_404(jalon_id)
    data = request.get_json()
    jalon.atteint = data['completed']
    db.session.commit()

    # Recalculate phase progress
    phase = jalon.phase
    total_jalons = len(phase.jalons)
    completed_jalons = sum(1 for j in phase.jalons if j.atteint)
    phase.progress = (completed_jalons / total_jalons) * 100 if total_jalons > 0 else 0
    db.session.commit()

    return jsonify({'success': True})

@projet_jalons_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_jalon(projet_id, phase_id):
    projet = Projet.query.get_or_404(projet_id)
    phase = Phase.query.get_or_404(phase_id)
    form = JalonForm()
    if form.validate_on_submit():
        jalon = Jalon(
            nom=form.nom.data,
            date=form.date.data,
            phase_id=phase_id,
            projet_id=projet_id
        )
        db.session.add(jalon)
        db.session.commit()
        flash('Jalon ajouté avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    return render_template('jalon_form.html', form=form, projet=projet, phase=phase, title="Ajouter un jalon")

@projet_jalons_bp.route('/<int:jalon_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_jalon(projet_id, phase_id, jalon_id):
    projet = Projet.query.get_or_404(projet_id)
    phase = Phase.query.get_or_404(phase_id)
    jalon = Jalon.query.get_or_404(jalon_id)
    form = JalonForm(obj=jalon)
    if request.method == 'POST':
        if form.validate_on_submit():
            jalon.nom = form.nom.data
            jalon.date = form.date.data
            # We don't have a field for atteint in the form, so we get it from the request
            jalon.atteint = request.form.get('atteint') == 'on'
            db.session.commit()
            flash('Jalon modifié avec succès!', 'success')
            return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    return render_template('jalon_form.html', form=form, projet=projet, phase=phase, title="Modifier un jalon", jalon=jalon)

@projet_jalons_bp.route('/<int:jalon_id>/modifier_statut', methods=['POST'])
def modifier_jalon_statut(projet_id, phase_id, jalon_id):
    logging.debug(f"Updating jalon {jalon_id} in phase {phase_id} of project {projet_id}")
    try:
        jalon = Jalon.query.get_or_404(jalon_id)
        data = request.get_json()

        if data is None:
            logging.error("No data provided in request")
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        if 'completed' not in data:
            logging.error("Missing 'completed' key in request data")
            return jsonify({'success': False, 'error': 'Missing "completed" key in data'}), 400

        jalon.atteint = data['completed']
        db.session.commit()
        logging.debug(f"Jalon {jalon_id} updated successfully. atteint set to {jalon.atteint}")

        # Recalculate phase progress
        phase = jalon.phase
        total_jalons = len(phase.jalons)
        completed_jalons = sum(1 for j in phase.jalons if j.atteint)
        phase.progress = (completed_jalons / total_jalons) * 100 if total_jalons > 0 else 0
        db.session.commit()
        logging.debug(f"Phase {phase_id} progress recalculated to {phase.progress}%")

        return jsonify({'success': True})

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projet_jalons_bp.route('/<int:jalon_id>/supprimer', methods=['POST'])
@login_required
def supprimer_jalon(projet_id, phase_id, jalon_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash("Erreur CSRF", 'danger')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    jalon = Jalon.query.get_or_404(jalon_id)
    db.session.delete(jalon)
    db.session.commit()
    flash('Jalon supprimé avec succès!', 'success')
    return redirect(url_for('projets.projet_detail', projet_id=projet_id))
