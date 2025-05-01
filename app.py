# c:\wamp\www\mon_compta_app\app.py
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv # Importe load_dotenv
from flask_wtf.csrf import CSRFProtect
# from flask_talisman import Talisman <- TODO
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
from controllers.whiteboard_controller import whiteboard_bp # Import the whiteboard blueprint
from controllers.plan_comptable_controller import plan_comptable_bp
from controllers.ecritures_controller import ecritures_bp
from controllers.notes_reunion_controller import notes_reunion_bp
from controllers.ocr_depenses_controller import ocr_depenses_bp
from models import *  # Import all models
#from models.clients import Client # Import the Client model
from models.organisations import Organisation
from models.users import User
from models.exercices import ExerciceComptable
from models.projets import Projet
from models.clients import Client
from datetime import date, datetime, timedelta
import os
from flask_migrate import Migrate  # Import Migrate

from werkzeug.utils import secure_filename

from utils.plan_comptable_initial_setup import generate_default_plan_comptable

load_dotenv(override=True)

app = Flask(__name__)

# Get the database URI from an environment variable
# Provide a default value ONLY for local development if absolutely necessary,
# but it's better to always require the environment variable.
database_uri = os.environ.get('DATABASE_URL')
print(f"DEBUG: DATABASE_URL lue = {database_uri}")
if not database_uri:
    # Option 1: Raise an error if the variable is not set (safer for production)
    raise ValueError("No DATABASE_URL set for Flask application")
    # Option 2: Use a default for local dev (less safe, use with caution)
    # print("WARNING: DATABASE_URL not set, using default local DB.")

app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)

# Get the secret key from an environment variable too!
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise ValueError("No SECRET_KEY set for Flask application")
app.config['SECRET_KEY'] = secret_key

app.config['MAX_LOGO_SIZE'] = 2 * 1024 * 1024 # 2MB max size for logo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Allowed extensions for logo

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads', 'attachments')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Create the folder if it doesn't exist

# Configuration du dossier static
app.static_folder = 'static'
app.static_url_path = '/static'

init_db(app)
from controllers.db_manager import db

migrate = Migrate(app, db)  # Initialize Migrate

csrf = CSRFProtect(app)     # Initialise CSRFProtect

# Register the blueprint
app.register_blueprint(projets_bp)
app.register_blueprint(users_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(organisations_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(compta_bp)
app.register_blueprint(projet_phases_bp)
app.register_blueprint(projet_jalons_bp)
app.register_blueprint(whiteboard_bp) # Register the whiteboard blueprint
app.register_blueprint(plan_comptable_bp)
app.register_blueprint(ecritures_bp)
app.register_blueprint(notes_reunion_bp)
app.register_blueprint(ocr_depenses_bp)

@app.route('/test-pen') # Vous pouvez choisir l'URL que vous voulez
def test_pen_page():
    """
    Affiche la page de test pour les pinceaux Fabric.js.
    """
    # Assurez-vous que le fichier 'test-pen.html' se trouve
    # dans votre dossier 'templates'
    return render_template('test-pen.html')

@app.route('/test/projet_detail')
def test_projet_detail():
    return render_template('test/test_projet_detail.html')

@app.route('/generer_facture/<int:transaction_id>')
@login_required
def generer_facture(transaction_id):
    transaction = FinancialTransaction.query.get_or_404(transaction_id)
    # Example using a function that generates the pdf
    pdf_data = generate_facturation_pdf(transaction)

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=facture_transaction_{}.pdf'.format(transaction_id)
    return response

if __name__ == '__main__':
    with app.app_context():
        organisation_creee = False # Initialiser la variable
        default_organisation = None
        default_user = None
        default_client = None # Initialiser default_client

        # --- Création Organisation (si besoin) ---
        if not Organisation.query.first():
            default_organisation = Organisation(
                designation="Studio Noble-Val",
                adresse="Num, localisation",
                code_postal="00000",
                ville="VILLE",
                telephone="070123456789",
                mail_contact="test@test.com",
                siret="12345678901234",
                tva_intracommunautaire=None,
                forme_juridique="Entreprise Individuelle"
            )
            db.session.add(default_organisation)
            try:
                db.session.commit()
                # Revenir à print
                print(f"INFO: Organisation par défaut (ID: {default_organisation.id}) créée avec succès.")
                organisation_creee = True
            except Exception as e:
                db.session.rollback()
                # Revenir à print
                print(f"ERREUR: Impossible de créer l'organisation par défaut: {e}")
                default_organisation = None
        else:
            default_organisation = Organisation.query.first()

        # --- Création User (si besoin) ---
        if not User.query.first() and default_organisation:

            default_mon = os.environ.get('DEFAULT_ADMIN_NOM')
            default_prenom = os.environ.get('DEFAULT_ADMIN_PRENOM')
            default_mail = os.environ.get('DEFAULT_ADMIN_MAIL')
            default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
            if not default_password:
                raise ValueError("La variable d'environnement DEFAULT_ADMIN_PASSWORD doit être définie pour créer l'utilisateur initial.")
            
            default_user = User(
                nom="Nom",
                prenom="Prenom",
                mail="nom.prenom@test.com",
                telephone="0123456789",
                organisation_id=default_organisation.id,
                is_super_admin=True,
                role="Admin"
            )
            default_user.set_password(default_password)
            db.session.add(default_user)
            try:
                db.session.commit()
                # Revenir à print
                print("INFO: Utilisateur Super Admin par défaut créé.")
            except Exception as e:
                 db.session.rollback()
                 # Revenir à print
                 print(f"ERREUR: Impossible de créer l'utilisateur par défaut: {e}")
        elif default_organisation:
             default_user = User.query.filter_by(organisation_id=default_organisation.id).first()
        else: # Si pas d'organisation
             # Revenir à print
             print("ERREUR: Impossible de créer l'utilisateur par défaut car aucune organisation n'existe.")


        # --- Génération Plan Comptable (si orga créée) ---
        if organisation_creee and default_organisation:
             # Revenir à print
             print(f"INFO: Tentative de génération du plan comptable pour l'organisation ID {default_organisation.id}...")
             comptes_crees = generate_default_plan_comptable(default_organisation)
             if comptes_crees is not None:
                 # Revenir à print
                 print(f"INFO: Génération du plan comptable terminée. {len(comptes_crees)} comptes ajoutés.")
             else:
                 # Revenir à print
                 print("ERREUR: La génération du plan comptable a échoué. Voir les logs pour plus de détails.")


        # --- Création Exercice (si besoin) ---
        if not ExerciceComptable.query.first() and default_organisation:
            # Revenir à print
            print("INFO: Aucun exercice trouvé, création de l'exercice pour l'année en cours...")
            current_year = date.today().year
            date_debut_exercice = date(current_year, 1, 1)
            date_fin_exercice = date(current_year, 12, 31)
            exercice_courant = ExerciceComptable(
                date_debut=date_debut_exercice,
                date_fin=date_fin_exercice,
                organisation_id=default_organisation.id
            )
            db.session.add(exercice_courant)
            try:
                db.session.commit()
                # Revenir à print
                print(f"INFO: Exercice pour l'année {current_year} créé.")
            except Exception as e:
                db.session.rollback()
                # Revenir à print
                print(f"ERREUR: Impossible de créer l'exercice par défaut pour l'année {current_year}: {e}")
        elif not default_organisation:
             # Revenir à print
             print("ERREUR: Impossible de créer l'exercice par défaut car aucune organisation n'existe.")


        # --- Création Client par Défaut (si besoin ET si orga existe) ---
        if default_organisation:
            client_existant = Client.query.filter_by(organisation_id=default_organisation.id).first()
            if not client_existant:
                # Revenir à print
                print("INFO: Aucun client trouvé pour l'organisation, création d'un client par défaut...")
                default_client = Client(
                    nom="Client Par Défaut",
                    adresse="1 Rue Exemple",
                    code_postal="75001",
                    ville="Paris",
                    telephone="0123456789",
                    mail="client.defaut@example.com",
                    organisation_id=default_organisation.id
                )
                db.session.add(default_client)
                try:
                    db.session.commit()
                    # Revenir à print
                    print(f"INFO: Client par défaut (ID: {default_client.id}) créé pour l'organisation ID: {default_organisation.id}.")
                except Exception as e:
                    db.session.rollback()
                    # Revenir à print
                    print(f"ERREUR: Impossible de créer le client par défaut: {e}")
                    default_client = None
            else:
                default_client = client_existant
                # Revenir à print (optionnel)
                # print(f"INFO: Un client (ID: {default_client.id}) existe déjà pour l'organisation ID: {default_organisation.id}.")
        else:
             # Revenir à print
             print("INFO: Aucune organisation trouvée, impossible de vérifier/créer un client par défaut.")


        # --- Création Projet par Défaut (si besoin ET si orga/user/client existent) ---
        if not Projet.query.first():
            final_organisation = Organisation.query.first()
            final_user = User.query.first()
            final_client = default_client # Utilise le client créé ou récupéré juste avant

            if final_organisation and final_user and final_client:
                # Revenir à print
                print("INFO: Aucun projet trouvé, création d'un projet par défaut...")
                try:
                    default_projet = Projet(
                        nom="Projet Par Défaut",
                        date_debut=date(2025, 1, 15),
                        date_fin=date(2025, 6, 30),
                        prix_total=1000.00,
                        organisation_id=final_organisation.id,
                        user_id=final_user.id,
                        client_id=final_client.id
                    )
                    db.session.add(default_projet)
                    db.session.commit()
                    # Revenir à print
                    print(f"INFO: Projet par défaut (ID: {default_projet.id}) créé.")
                except Exception as e:
                    db.session.rollback()
                    # Revenir à print
                    print(f"ERREUR: Impossible de créer le projet par défaut: {e}")
            else:
                missing = []
                if not final_organisation: missing.append("organisation")
                if not final_user: missing.append("utilisateur")
                if not final_client: missing.append("client")
                # Revenir à print
                print(f"ERREUR: Impossible de créer le projet par défaut car l'{' ou '.join(missing)} manque.")

    app.run()