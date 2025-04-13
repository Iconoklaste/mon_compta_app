# c:\wamp\www\mon_compta_app\app.py
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify, session, abort
from flask_wtf.csrf import CSRFProtect
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
from models import *  # Import all models
#from models.clients import Client # Import the Client model
from models.organisations import Organisation
from models.users import User
from models.exercices import ExerciceComptable
from models.projets import Projet
from models.clients import Client
from datetime import date, datetime
import os
from flask_migrate import Migrate  # Import Migrate

from werkzeug.utils import secure_filename

from utils.plan_comptable_initial_setup import generate_default_plan_comptable

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

@app.route('/test/projet_detail')
def test_projet_detail():
    return render_template('test/test_projet_detail.html')

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


if __name__ == '__main__':
    with app.app_context():
        # db.create_all() # Remove this line, Flask-Migrate will handle database creation
        # Create a default organization if none exists
        if not Organisation.query.first():
            default_organisation = Organisation(
                designation="Studio Noble-Val",
                adresse="14, Place de la Fontaine",
                code_postal="82330",
                ville="VAREN",
                telephone="0768981844",
                mail_contact="tjacquemot@gmail.com",
                siret="12345678901234",  # Example SIRET
                tva_intracommunautaire=None,  # Optional, can be None
                forme_juridique="Entreprise Individuelle"  # Example legal form
            )
            db.session.add(default_organisation)
            try:
                db.session.commit()
                print(f"INFO: Organisation par défaut (ID: {default_organisation.id}) créée avec succès.")
                organisation_creee = True # On l'a créée
            except Exception as e:
                db.session.rollback()
                print(f"ERREUR: Impossible de créer l'organisation par défaut: {e}")
                # Si l'organisation ne peut être créée, on ne peut pas continuer
                # Peut-être sortir ou gérer l'erreur autrement
                default_organisation = None # Assure qu'on ne l'utilise pas plus loin


        # Create a default user if none exists
        if not User.query.first():
            # On récupère l'organisation par défaut (qui a dû être créée juste avant si elle n'existait pas)
            default_organisation = Organisation.query.first()
            if default_organisation: # S'assurer qu'on a bien une organisation
                default_user = User(
                    nom="Jacquemot",
                    prenom="Thomas",
                    mail="tjacquemot@gmail.com",
                    telephone="0768981844",
                    organisation_id=default_organisation.id,
                    is_super_admin=True,  # <--- AJOUTE CETTE LIGNE
                    role="Admin" # Tu peux aussi définir un rôle explicite si besoin
                )
                default_user.set_password("test")  # Set a default password
                db.session.add(default_user)
                try:
                    db.session.commit()
                    print("INFO: Utilisateur Super Admin par défaut créé.")
                except Exception as e:
                     db.session.rollback()
                     print(f"ERREUR: Impossible de créer l'utilisateur par défaut: {e}")
            else:
                print("ERREUR: Impossible de créer l'utilisateur par défaut car aucune organisation n'existe (ou n'a pu être créée).")

                # --- APPEL DE LA GENERATION DU PLAN COMPTABLE ---
            # On génère le plan comptable SEULEMENT si on vient de créer l'organisation
            # ET si elle a bien été créée (default_organisation n'est pas None)
            if organisation_creee and default_organisation:
                print(f"INFO: Tentative de génération du plan comptable pour l'organisation ID {default_organisation.id}...")
                comptes_crees = generate_default_plan_comptable(default_organisation)
                if comptes_crees is not None:
                    print(f"INFO: Génération du plan comptable terminée. {len(comptes_crees)} comptes ajoutés.")
                else:
                    print("ERREUR: La génération du plan comptable a échoué. Voir les logs pour plus de détails.")
            # --- FIN DE L'APPEL ---

        # Create an exercice for the current year if none exists
        if not ExerciceComptable.query.first():
            # Récupère l'organisation (soit celle existante, soit celle qu'on vient de créer)
            organisation_pour_exercice = Organisation.query.first()
            if organisation_pour_exercice:
                print("INFO: Aucun exercice trouvé, création de l'exercice pour l'année en cours...")
                # Récupère l'année en cours
                current_year = date.today().year
                # Définit les dates de début et de fin pour l'année en cours
                date_debut_exercice = date(current_year, 1, 1)
                date_fin_exercice = date(current_year, 12, 31)

                exercice_courant = ExerciceComptable(
                    date_debut=date_debut_exercice,
                    date_fin=date_fin_exercice,
                    organisation_id=organisation_pour_exercice.id
                    # Le statut par défaut est 'Ouvert' (défini dans le modèle)
                )
                db.session.add(exercice_courant)
                try:
                    db.session.commit()
                    print(f"INFO: Exercice pour l'année {current_year} créé.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERREUR: Impossible de créer l'exercice par défaut pour l'année {current_year}: {e}")
            else:
                print("ERREUR: Impossible de créer l'exercice par défaut car aucune organisation n'existe.")



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
