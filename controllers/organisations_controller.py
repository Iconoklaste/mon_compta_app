from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Organisation, User
from werkzeug.utils import secure_filename

organisations_bp = Blueprint('organisations', __name__, url_prefix='/organisations')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@organisations_bp.route('/ajouter_organisation', methods=['POST'])
@login_required
def ajouter_organisation():
    data = request.get_json()
    designation = data.get('designation')
    adresse = data.get('adresse')
    code_postal = data.get('code_postal')
    ville = data.get('ville')
    telephone = data.get('telephone')
    mail_contact = data.get('mail_contact')
    logo = data.get('logo')
    if designation:
        new_organisation = Organisation(designation=designation, adresse=adresse, code_postal=code_postal, ville=ville, telephone=telephone, mail_contact=mail_contact, logo=logo)
        db.session.add(new_organisation)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

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
