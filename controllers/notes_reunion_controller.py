# routes/notes_reunion.py (nouveau fichier)

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from controllers.users_controller import login_required
from controllers.db_manager import db
from models import Projet, NoteReunion
from forms.forms import NoteReunionForm
from datetime import datetime, timezone

notes_reunion_bp = Blueprint('notes_reunion', __name__, url_prefix='/projets/<int:projet_id>/notes')

# --- Helper function pour vérifier l'accès au projet (exemple) ---
def check_projet_access(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    # Ajoute ici ta logique de permission si nécessaire
    # Par exemple, vérifier si current_user est membre du projet
    # if projet.client_id != current_user.id and not current_user.is_admin: # Exemple simple
    #     abort(403)
    return projet

# --- Route pour ajouter une note ---
@notes_reunion_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required # Assure-toi que l'utilisateur est connecté
def ajouter_note(projet_id):
    projet = check_projet_access(projet_id)
    form = NoteReunionForm()

    if form.validate_on_submit():
        form_date = form.date.data
        date_reunion_dt_naive_utc = datetime.combine(form_date, datetime.min.time())
        nouvelle_note = NoteReunion(
            date=date_reunion_dt_naive_utc,
            contenu=form.contenu.data, # Le contenu HTML vient du Rich Text Editor
            projet_id=projet.id
        )
        try:
            db.session.add(nouvelle_note)
            db.session.commit()
            flash('Note de réunion ajoutée avec succès.', 'success')
            # Redirige vers l'onglet des notes dans projet_detail
            return redirect(url_for('projets.projet_detail', projet_id=projet.id, _anchor='tab3-content'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout de la note : {e}', 'danger')



    return render_template('ajouter_modifier_note.html',
                           title=f"Ajouter une note - {projet.nom}",
                           form=form,
                           projet=projet,
                           mode='ajouter')

# --- Route pour modifier une note ---
@notes_reunion_bp.route('/<int:note_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_note(projet_id, note_id):
    projet = check_projet_access(projet_id)
    note = NoteReunion.query.filter_by(id=note_id, projet_id=projet.id).first_or_404()
    form = NoteReunionForm(obj=note) # Pré-remplit le formulaire avec les données de la note

    if form.validate_on_submit():
        try:
            form_date = form.date.data
            date_reunion_dt_naive_utc = datetime.combine(form_date, datetime.min.time())
            note.date = date_reunion_dt_naive_utc
            note.contenu = form.contenu.data # Récupère le HTML de l'éditeur
            note.updated_at = datetime.now(timezone.utc) # Met à jour manuellement si besoin
            db.session.commit()
            flash('Note de réunion modifiée avec succès.', 'success')
            return redirect(url_for('projets.projet_detail', projet_id=projet.id, _anchor='tab3-content'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de la note : {e}', 'danger')

    return render_template('ajouter_modifier_note.html',
                           title=f"Modifier la note - {projet.nom}",
                           form=form,
                           projet=projet,
                           note=note,
                           mode='modifier')

# --- Route pour supprimer une note ---
@notes_reunion_bp.route('/<int:note_id>/supprimer', methods=['POST']) # Utilise POST pour la suppression
@login_required
def supprimer_note(projet_id, note_id):
    # Vérifie le token CSRF si tu utilises WTForms CSRFProtect
    # (Normalement géré automatiquement si le form submit vient d'un form WTForms)
    projet = check_projet_access(projet_id)
    note = NoteReunion.query.filter_by(id=note_id, projet_id=projet.id).first_or_404()

    try:
        db.session.delete(note)
        db.session.commit()
        flash('Note de réunion supprimée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la note : {e}', 'danger')

    return redirect(url_for('projets.projet_detail', projet_id=projet.id, _anchor='tab3-content'))

