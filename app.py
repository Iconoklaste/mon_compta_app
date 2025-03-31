# c:\wamp\www\mon_compta_app\app.py
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify, session, abort
from controllers.users_controller import login_required, users_bp
from controllers.db_manager import init_db
from controllers.projets_controller import projets_bp  # Import the blueprint
from controllers.facturation import generate_facturation_pdf # Import the function from facturation.py
from controllers.clients_controller import clients_bp
from controllers.organisations_controller import organisations_bp
from controllers.transactions_controller import transactions_bp
from controllers.compta_controller import compta_bp
from controllers.projet_phases import projet_phases_bp
from controllers.projet_jalons import projet_jalons_bp
from models import *  # Import all models
#from models.clients import Client # Import the Client model
from models.organisations import Organisation
from models.users import User
from models.exercices import ExerciceComptable
from models.projets import Projet
from datetime import date, datetime
import os
from flask_migrate import Migrate  # Import Migrate

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.expanduser("~"), 'compta.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Add a secret key
app.config['MAX_LOGO_SIZE'] = 2 * 1024 * 1024 # 2MB max size for logo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Allowed extensions for logo

# Configuration du dossier static
app.static_folder = 'static'
app.static_url_path = '/static'

init_db(app)
from controllers.db_manager import db

migrate = Migrate(app, db)  # Initialize Migrate

# Register the blueprint
app.register_blueprint(projets_bp)
app.register_blueprint(users_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(organisations_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(compta_bp)
app.register_blueprint(projet_phases_bp)
app.register_blueprint(projet_jalons_bp)


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

# Stockage temporaire (à remplacer par une base de données)
whiteboard_data = {}

@app.route('/whiteboard')
def whiteboard():
    return render_template('whiteboard.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    whiteboard_data['state'] = data
    return jsonify({'message': 'Whiteboard sauvegardé'})

@app.route('/load', methods=['GET'])
def load():
    if 'state' in whiteboard_data:
        return jsonify(whiteboard_data['state'])
    else:
        return jsonify({'message': 'Aucune donnée sauvegardée'})

if __name__ == '__main__':
    with app.app_context():
        # db.create_all() # Remove this line, Flask-Migrate will handle database creation
        # Create a default organization if none exists
        if not Organisation.query.first():
            default_organisation = Organisation(
                designation="Default Organisation",
                adresse="Default Address",
                code_postal="00000",
                ville="Default City",
                telephone="0123456789",
                mail_contact="default@example.com",
                siret="12345678901234",  # Example SIRET
                tva_intracommunautaire=None,  # Optional, can be None
                forme_juridique="SARL"  # Example legal form
            )
            db.session.add(default_organisation)
            db.session.commit()

        # Create a default user if none exists
        if not User.query.first():
            default_organisation = Organisation.query.first()
            default_user = User(
                nom="Jacquemot",
                prenom="Thomas",
                mail="tjacquemot@gmail.com",
                telephone="0123456789",
                organisation_id=default_organisation.id # change organisation to organisation_id
            )
            default_user.set_password("test")  # Set a default password
            db.session.add(default_user)
            db.session.commit()
        
        # Create an exercice for 2025 if none exists
        if not ExerciceComptable.query.first():
            default_organisation = Organisation.query.first()
            exercice_2025 = ExerciceComptable(
                date_debut=date(2025, 1, 1),
                date_fin=date(2025, 12, 31),
                organisation_id=default_organisation.id
            )
            db.session.add(exercice_2025)
            db.session.commit()

        # Create a default project if none exists
        if not Projet.query.first():
            default_organisation = Organisation.query.first()
            default_user = User.query.first()
            exercice_2025 = ExerciceComptable.query.first()
            # Create a default client
            default_client = Client(
                nom="Default Client",
                adresse="Client Address",
                code_postal="12345",
                ville="Client City",
                telephone="9876543210",
                mail="client@example.com"
            )
            db.session.add(default_client)
            db.session.commit()

            default_projet = Projet(
                nom="Default Project",
                date_debut=date(2025, 1, 15),
                date_fin=date(2025, 6, 30),
                prix_total=1000.00,
                organisation_id=default_organisation.id, # change organisation to organisation_id
                user_id=default_user.id, # change user to user_id
                client_id=default_client.id
            )
            db.session.add(default_projet)
            db.session.commit()
        pass
    app.run(debug=True)
