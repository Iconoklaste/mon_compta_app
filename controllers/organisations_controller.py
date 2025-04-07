from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session, current_app, flash
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Organisation, User
from forms.forms import OrganisationForm  # Import the OrganisationForm
from werkzeug.utils import secure_filename
from io import BytesIO
import os

organisations_bp = Blueprint('organisations', __name__, url_prefix='/organisations')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@organisations_bp.route('/ajouter_organisation', methods=['POST'])
def ajouter_organisation():
    form = OrganisationForm()  # Create an instance of the form

    if form.validate_on_submit():
        try:
            logo_data = None
            logo_mimetype = None

            if form.logo.data:
                try:
                    logo_data = form.logo.data.read()
                    logo_mimetype = form.logo.data.mimetype
                except ValueError as e:
                    return jsonify({'success': False, 'error': str(e)}), 400

            # Création de l'organisation
            new_organisation = Organisation(
                designation=form.designation.data,
                siret=form.siret.data,
                exonere_tva=form.exonere_tva.data,
                tva_intracommunautaire=form.tva_intracommunautaire.data,
                forme_juridique=form.forme_juridique.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail_contact=form.mail_contact.data,
                iban=form.iban.data,
                bic=form.bic.data,
                logo=logo_data,
                logo_mimetype=logo_mimetype
            )

            db.session.add(new_organisation)
            db.session.commit()

            return jsonify({'success': True, 'organisation_id': new_organisation.id}), 201  # 201 Created
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        # Handle form validation errors
        errors = {field: errors for field, errors in form.errors.items()}
        return jsonify({'success': False, 'errors': errors}), 400

@organisations_bp.route('/modifier_organisation', methods=['GET', 'POST'])
@login_required
def modifier_organisation():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    form = OrganisationForm(obj=organisation)

    if form.validate_on_submit():
        organisation.designation = form.designation.data
        organisation.siret = form.siret.data
        organisation.exonere_tva = form.exonere_tva.data
        organisation.tva_intracommunautaire = form.tva_intracommunautaire.data
        organisation.forme_juridique = form.forme_juridique.data
        organisation.adresse = form.adresse.data
        organisation.code_postal = form.code_postal.data
        organisation.ville = form.ville.data
        organisation.telephone = form.telephone.data
        organisation.mail_contact = form.mail_contact.data
        organisation.iban = form.iban.data
        organisation.bic = form.bic.data

        # Handle logo upload
        if form.logo.data:
            try:
                organisation.logo = form.logo.data.read()
                organisation.logo_mimetype = form.logo.data.mimetype
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('modifier_organisation.html', organisation=organisation, form=form)

        db.session.commit()
        flash('Organisation modifiée avec succès!', 'success')
        return redirect(url_for('users.index'))
    else:
        # Handle form validation errors
        return render_template('modifier_organisation.html', organisation=organisation, form=form)

@organisations_bp.route('/get_logo/<int:organisation_id>', endpoint='get_logo')
def get_logo(organisation_id):
    organisation = Organisation.query.get_or_404(organisation_id)
    if organisation.logo:
        response = make_response(organisation.logo)
        response.headers.set('Content-Type', organisation.logo_mimetype)
        return response
    else:
        return "Logo not found", 404
