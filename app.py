# c:\wamp\www\mon_compta_app\app.py
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify, session, abort
from controllers.db_manager import init_db, db
from controllers.projets_controller import projets_bp  # Import the blueprint
from models import *  # Import all models
from models.clients import Client # Import the Client model
from datetime import date
import os
from flask_migrate import Migrate  # Import Migrate
from controllers.facturation import generate_facturation_pdf # Import the function from facturation.py
from functools import wraps
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.expanduser("~"), 'compta.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Add a secret key
app.config['MAX_LOGO_SIZE'] = 2 * 1024 * 1024 # 2MB max size for logo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Allowed extensions for logo

init_db(app)

migrate = Migrate(app, db)  # Initialize Migrate

# Register the blueprint
app.register_blueprint(projets_bp)

# Removed the generate_pdf function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    organisations = Organisation.query.all()
    users = User.query.all()
    return render_template('index.html', organisations=organisations, users=users)

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(mail=email).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return redirect(url_for('projets'))
    else:
        return "Invalid email or password", 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/projets')
@login_required
def projets():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    projets = Projet.query.filter_by(user_id=user_id).all()
    return render_template('projets.html', projets=projets)

@app.route('/projet/<int:projet_id>')
@login_required
def projet_detail(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    transactions = Transaction.query.filter_by(projet_id=projet_id).all()
    total_billed = sum(transaction.montant for transaction in transactions)
    remaining_to_bill = projet.prix_total - total_billed
    return render_template('projet_detail.html',
                           projet=projet,
                           transactions=transactions,
                           remaining_to_bill=remaining_to_bill)

@app.route('/ajouter_projet', methods=['GET', 'POST'])
@login_required
def ajouter_projet():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    clients = Client.query.all() # Get all clients
    status_options = ["En attente", "En cours", "Terminé", "Annulé"] # Add this line
    if request.method == 'POST':
        nom = request.form['nom']
        # client = request.form['client'] # Removed this line
        client_id = request.form['client_id'] # Get the client_id
        date_debut_str = request.form['date_debut']
        date_fin_str = request.form['date_fin']
        statut = request.form['statut']
        prix_total = int(request.form['prix_total']) if request.form['prix_total'] else 0
        date_debut = date.fromisoformat(date_debut_str) if date_debut_str else None
        date_fin = date.fromisoformat(date_fin_str) if date_fin_str else None
        organisation = Organisation.query.first()

        # Get the client object
        client = Client.query.get(client_id)

        nouveau_projet = Projet(nom=nom, date_debut=date_debut, date_fin=date_fin, statut=statut, prix_total=prix_total, organisation=organisation, user=user, client_obj=client) # Add client_obj
        db.session.add(nouveau_projet)
        db.session.commit()
        return redirect(url_for('projets'))

    return render_template('ajouter_projet.html', clients=clients, status_options=status_options) # Pass status_options to the template



@app.route('/ajouter_client', methods=['POST'])
def ajouter_client():
    data = request.get_json()
    nom = data.get('nom')
    adresse = data.get('adresse')
    code_postal = data.get('code_postal')
    ville = data.get('ville')
    telephone = data.get('telephone')
    mail = data.get('mail')

    if nom:
        new_client = Client(nom=nom, adresse=adresse, code_postal=code_postal, ville=ville, telephone=telephone, mail=mail)
        db.session.add(new_client)
        db.session.commit()
        return jsonify({'success': True, 'client_id': new_client.id})
    return jsonify({'success': False})

@app.route('/ajouter_transaction/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_transaction(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    if request.method == 'POST':
        date_str = request.form['date']
        type = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        mode_paiement = request.form['mode_paiement']

        date_transaction = date.fromisoformat(date_str)
        organisation = Organisation.query.first()
        user = User.query.first()

        nouvelle_transaction = Transaction(date=date_transaction, type=type, montant=montant, description=description, mode_paiement=mode_paiement, projet_id=projet_id, organisation=organisation, user=user)
        db.session.add(nouvelle_transaction)
        db.session.commit()
        return redirect(url_for('projet_detail', projet_id=projet_id))

    return render_template('ajouter_transaction.html', projet=projet)

@app.route('/generer_facture/<int:transaction_id>')
@login_required
def generer_facture(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    # Example using a function that generates the pdf
    pdf_data = generate_facturation_pdf(transaction)

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=facture_transaction_{}.pdf'.format(transaction_id)
    return response

@app.route('/ajouter_user', methods=['GET', 'POST'])
def ajouter_user():
    organisations = Organisation.query.all()
    user_organisation = Organisation.query.first()
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        mail = request.form['mail']
        telephone = request.form['telephone']
        password = request.form['password']
        organisation_designation = request.form['organisation']

        organisation = Organisation.query.filter_by(designation=organisation_designation).first()
        if not organisation:
            return "Organisation not found", 400

        new_user = User(nom=nom, prenom=prenom, mail=mail, telephone=telephone, organisation=organisation)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('ajouter_user.html', organisations=organisations, user_organisation=user_organisation)

@app.route('/ajouter_organisation', methods=['POST'])
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

@app.route('/modifier_profil', methods=['GET', 'POST'])
@login_required
def modifier_profil():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.nom = request.form['nom']
        user.prenom = request.form['prenom']
        user.mail = request.form['mail']
        user.telephone = request.form['telephone']
        if request.form['password']:
            user.set_password(request.form['password'])
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('modifier_profil.html', user=user)

@app.route('/modifier_organisation', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))

    return render_template('modifier_organisation.html', organisation=organisation)

@app.route('/get_logo/<int:organisation_id>')
def get_logo(organisation_id):
    organisation = Organisation.query.get_or_404(organisation_id)
    if organisation.logo:
        response = make_response(organisation.logo)
        response.headers.set('Content-Type', organisation.logo_mimetype)
        return response
    else:
        return "Logo not found", 404

if __name__ == '__main__':
    with app.app_context():
        # db.create_all() # Remove this line, Flask-Migrate will handle database creation
        # Create a default organization if none exists
        if not Organisation.query.first():
            default_organisation = Organisation(designation="Default Organisation", adresse="Default Address", code_postal="00000", ville="Default City", telephone="0123456789", mail_contact="default@example.com")
            db.session.add(default_organisation)
            db.session.commit()
        pass
    app.run(debug=True)
