# transactions_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Projet, Transaction, User, ExerciceComptable, Organisation
from controllers.db_manager import db
from datetime import date
from controllers.users_controller import login_required

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@transactions_bp.route('/ajouter/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_transaction(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Calculate the total billed amount for the project
    total_billed = sum(transaction.montant for transaction in projet.transactions)
    remaining_to_bill = projet.prix_total - total_billed

    # Get existing fiscal years for the organization
    exercices = ExerciceComptable.query.filter_by(organisation_id=organisation.id).all()
    
    if request.method == 'POST':
        date_str = request.form['date']
        type_transaction = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        mode_paiement = request.form['mode_paiement']
        date_transaction = date.fromisoformat(date_str)
        exercice_id = request.form.get('exercice_id')
        
        # Check if a new fiscal year needs to be created
        if exercice_id == 'new':
            date_debut_exercice_str = request.form.get('date_debut_exercice')
            date_fin_exercice_str = request.form.get('date_fin_exercice')
            
            if not date_debut_exercice_str or not date_fin_exercice_str:
                flash("Veuillez renseigner les dates de début et de fin de l'exercice.", 'danger')
                return render_template('ajouter_transaction.html', projet=projet, remaining_to_bill=remaining_to_bill, exercices=exercices, date=date_str, type=type_transaction, montant=montant, description=description, mode_paiement=mode_paiement)

            date_debut_exercice = date.fromisoformat(date_debut_exercice_str)
            date_fin_exercice = date.fromisoformat(date_fin_exercice_str)

            # Correct way to create ExerciceComptable
            new_exercice = ExerciceComptable(date_debut=date_debut_exercice, date_fin=date_fin_exercice, organisation_id=organisation.id)
            db.session.add(new_exercice)
            db.session.flush()  # Get the ID of the new exercice
            exercice_id = new_exercice.id
            db.session.commit()
            exercices = ExerciceComptable.query.filter_by(organisation_id=organisation.id).all()
        
        # Validation: Check if the transaction amount exceeds the remaining amount
        if montant > remaining_to_bill:
            flash(f"Le montant de la transaction ({montant} €) dépasse le montant restant à facturer ({remaining_to_bill} €) pour ce projet.", 'danger')
            # Repopulate the form with the submitted data
            return render_template('ajouter_transaction.html', projet=projet,
                                   date=date_str, type=type_transaction, montant=montant,
                                   description=description, mode_paiement=mode_paiement, remaining_to_bill=remaining_to_bill, exercices=exercices)

        transaction = Transaction(
            date=date_transaction,
            type=type_transaction,
            montant=montant,
            description=description,
            mode_paiement=mode_paiement,
            projet_id=projet_id,
            organisation=organisation,
            user=user,
            exercice_id=exercice_id if exercice_id != 'new' else None
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction ajoutée avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id, remaining_to_bill=remaining_to_bill))
    return render_template('ajouter_transaction.html', projet=projet, remaining_to_bill=remaining_to_bill, exercices=exercices)
