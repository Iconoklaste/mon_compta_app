# c:\wamp\www\mon_compta_app\app.py
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, jsonify, session, abort
from controllers.users_controller import login_required, users_bp
from controllers.db_manager import init_db
from controllers.projets_controller import projets_bp  # Import the blueprint
from controllers.facturation import generate_facturation_pdf # Import the function from facturation.py
from controllers.clients_controller import clients_bp
from controllers.organisations_controller import organisations_bp
from controllers.transactions_controller import transactions_bp
from models import *  # Import all models
#from models.clients import Client # Import the Client model
from models.organisations import Organisation
from models.users import User
from datetime import date
import os
from flask_migrate import Migrate  # Import Migrate

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.expanduser("~"), 'compta.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Add a secret key
app.config['MAX_LOGO_SIZE'] = 2 * 1024 * 1024 # 2MB max size for logo
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Allowed extensions for logo

init_db(app)
from controllers.db_manager import db

migrate = Migrate(app, db)  # Initialize Migrate

# Register the blueprint
app.register_blueprint(projets_bp)
app.register_blueprint(users_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(organisations_bp)
app.register_blueprint(transactions_bp)






# @app.route('/ajouter_transaction/<int:projet_id>', methods=['GET', 'POST'])
# @login_required
# def ajouter_transaction(projet_id):
#     projet = Projet.query.get_or_404(projet_id)
#     if request.method == 'POST':
#         date_str = request.form['date']
#         type = request.form['type']
#         montant = float(request.form['montant'])
#         description = request.form['description']
#         mode_paiement = request.form['mode_paiement']

#         date_transaction = date.fromisoformat(date_str)
#         organisation = Organisation.query.first()
#         user = User.query.first()

#         nouvelle_transaction = Transaction(date=date_transaction, type=type, montant=montant, description=description, mode_paiement=mode_paiement, projet_id=projet_id, organisation=organisation, user=user)
#         db.session.add(nouvelle_transaction)
#         db.session.commit()
#         return redirect(url_for('projets.projet_detail', projet_id=projet_id))

#     return render_template('ajouter_transaction.html', projet=projet)

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



# Removed the get_logo function

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
        pass
    app.run(debug=True)
