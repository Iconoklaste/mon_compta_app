from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Organisation, User
from werkzeug.utils import secure_filename
from io import BytesIO

organisations_bp = Blueprint('organisations', __name__, url_prefix='/organisations')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@organisations_bp.route('/ajouter_organisation', methods=['POST'])
def ajouter_organisation():
    try:
        designation = request.form.get('designation')
        adresse = request.form.get('adresse')
        code_postal = request.form.get('code_postal')
        ville = request.form.get('ville')
        telephone = request.form.get('telephone')
        mail_contact = request.form.get('mail_contact')
        logo = request.files.get('logo')

        # Validation des données
        if not all([designation, adresse, code_postal, ville, telephone, mail_contact]):
            return jsonify({'success': False, 'error': 'Tous les champs sont obligatoires.'}), 400

        logo_data = None
        logo_mimetype = None

        if logo and logo.filename != '' and allowed_file(logo.filename):
            try:
                logo_data = logo.read()
                logo_mimetype = logo.mimetype
            except ValueError as e:
                return str(e), 400
        elif logo and logo.filename != '':
            return "File type not allowed", 400

        # Création de l'organisation
        new_organisation = Organisation(
            designation=designation,
            adresse=adresse,
            code_postal=code_postal,
            ville=ville,
            telephone=telephone,
            mail_contact=mail_contact,
            logo=logo_data,
            logo_mimetype=logo_mimetype
        )

        db.session.add(new_organisation)
        db.session.commit()

        return jsonify({'success': True, 'organisation_id': new_organisation.id}), 201  # 201 Created
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@organisations_bp.route('/modifier_organisation', methods=['GET', 'POST'])
@login_required
def modifier_organisation():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    if request.method == 'POST':
        organisation.designation = request.form['designation']
        organisation.adresse = request.form['adresse']
        organisation.code_postal = request.form['code_postal']
        organisation.ville = request.form['ville']
        organisation.telephone = request.form['telephone']
        organisation.mail_contact = request.form['mail_contact']
        organisation.iban = request.form['iban']
        organisation.bic = request.form['bic']
        organisation.exonere_tva = 'exonere_tva' in request.form  # Check if the checkbox is checked

        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    organisation.logo = file.read()
                    organisation.logo_mimetype = file.mimetype
                except ValueError as e:
                    return str(e), 400
            elif file and file.filename != '':
                return "File type not allowed", 400

        db.session.commit()
        return redirect(url_for('users.index'))

    return render_template('modifier_organisation.html', organisation=organisation)

@organisations_bp.route('/get_logo/<int:organisation_id>', endpoint='get_logo')
def get_logo(organisation_id):
    organisation = Organisation.query.get_or_404(organisation_id)
    if organisation.logo:
        response = make_response(organisation.logo)
        response.headers.set('Content-Type', organisation.logo_mimetype)
        return response
    else:
        return "Logo not found", 404
