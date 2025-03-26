from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
from controllers.db_manager import init_db, db
from controllers.projets_controller import projets_bp  # Import the blueprint
from models.projets import Projet
from models.transactions import Transaction
from datetime import date
import os
from flask_migrate import Migrate  # Import Migrate
from controllers.facturation import generate_facturation_pdf # Import the function from facturation.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.expanduser("~"), 'compta.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Add a secret key

init_db(app)

migrate = Migrate(app, db)  # Initialize Migrate

# Register the blueprint
app.register_blueprint(projets_bp)

# Removed the generate_pdf function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projets')
def projets():
    projets = Projet.query.all()
    return render_template('projets.html', projets=projets)

@app.route('/projet/<int:projet_id>')
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
def ajouter_projet():
    if request.method == 'POST':
        nom = request.form['nom']
        client = request.form['client']
        date_debut_str = request.form['date_debut']
        date_fin_str = request.form['date_fin']
        statut = request.form['statut']
        prix_total = int(request.form['prix_total']) if request.form['prix_total'] else 0
        date_debut = date.fromisoformat(date_debut_str) if date_debut_str else None
        date_fin = date.fromisoformat(date_fin_str) if date_fin_str else None

        nouveau_projet = Projet(nom=nom, client=client, date_debut=date_debut, date_fin=date_fin, statut=statut, prix_total=prix_total)
        db.session.add(nouveau_projet)
        db.session.commit()
        return redirect(url_for('projets'))

    return render_template('ajouter_projet.html')

@app.route('/ajouter_transaction/<int:projet_id>', methods=['GET', 'POST'])
def ajouter_transaction(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    if request.method == 'POST':
        date_str = request.form['date']
        type = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        mode_paiement = request.form['mode_paiement']

        date_transaction = date.fromisoformat(date_str)

        nouvelle_transaction = Transaction(date=date_transaction, type=type, montant=montant, description=description, mode_paiement=mode_paiement, projet_id=projet_id)
        db.session.add(nouvelle_transaction)
        db.session.commit()
        return redirect(url_for('projet_detail', projet_id=projet_id))

    return render_template('ajouter_transaction.html', projet=projet)



@app.route('/generer_facture/<int:transaction_id>')
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
        pass
    app.run(debug=True)
