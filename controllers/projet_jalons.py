# c:\wamp\www\mon_compta_app\controllers\projet_jalons.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from controllers.db_manager import db
from models import Jalon, Projet, Phase
from forms.forms import JalonForm
from controllers.users_controller import login_required
from datetime import date

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
    if form.validate_on_submit():
        jalon.nom = form.nom.data
        jalon.date = form.date.data
        db.session.commit()
        flash('Jalon modifié avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))
    return render_template('jalon_form.html', form=form, projet=projet, phase=phase, title="Modifier un jalon")

@projet_jalons_bp.route('/<int:jalon_id>/supprimer', methods=['POST'])
@login_required
def supprimer_jalon(projet_id, phase_id, jalon_id):
    jalon = Jalon.query.get_or_404(jalon_id)
    db.session.delete(jalon)
    db.session.commit()
    flash('Jalon supprimé avec succès!', 'success')
    return redirect(url_for('projets.projet_detail', projet_id=projet_id))
