# transactions_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Projet, Transaction, User
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

    if request.method == 'POST':
        date_str = request.form['date']
        type_transaction = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        mode_paiement = request.form['mode_paiement']
        date_transaction = date.fromisoformat(date_str)

        # Validation: Check if the transaction amount exceeds the remaining amount
        if montant > remaining_to_bill:
            flash(f"Le montant de la transaction ({montant} €) dépasse le montant restant à facturer ({remaining_to_bill} €) pour ce projet.", 'danger')
            # Repopulate the form with the submitted data
            return render_template('ajouter_transaction.html', projet=projet,
                                   date=date_str, type=type_transaction, montant=montant,
                                   description=description, mode_paiement=mode_paiement, remaining_to_bill=remaining_to_bill)

        transaction = Transaction(
            date=date_transaction,
            type=type_transaction,
            montant=montant,
            description=description,
            mode_paiement=mode_paiement,
            projet_id=projet_id,
            organisation=organisation,
            user=user
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction ajoutée avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id, remaining_to_bill=remaining_to_bill))
    return render_template('ajouter_transaction.html', projet=projet, remaining_to_bill=remaining_to_bill)
