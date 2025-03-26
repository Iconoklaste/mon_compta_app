from flask import Blueprint, render_template, redirect, url_for, request
from models.projets import Projet
from controllers.db_manager import db
from forms.forms import ProjetForm

projets_bp = Blueprint('projets', __name__)

@projets_bp.route('/projet/<int:projet_id>/modifier', methods=['GET', 'POST'])
def modifier_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    form = ProjetForm(obj=projet)  # Populate the form with the project's data

    if form.validate_on_submit():
        projet.nom = form.nom.data
        projet.client = form.client.data
        projet.date_debut = form.date_debut.data
        projet.date_fin = form.date_fin.data
        projet.statut = form.statut.data
        projet.prix_total = form.prix_total.data

        db.session.commit()
        return redirect(url_for('projet_detail', projet_id=projet.id))

    return render_template('projet_edit.html', projet=projet, form=form)

@projets_bp.route('/projet/<int:projet_id>/supprimer', methods=['GET'])
def supprimer_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    # Delete related transactions first (if necessary)
    for transaction in projet.transactions:
        db.session.delete(transaction)
    db.session.delete(projet)
    db.session.commit()
    return redirect(url_for('index')) # Or another appropriate route