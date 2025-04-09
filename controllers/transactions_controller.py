# controllers/transactions_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Projet, Transaction, User, ExerciceComptable, Organisation
from controllers.db_manager import db
# 'date' from datetime might not be needed if form handles defaults
# from datetime import date 
from controllers.users_controller import login_required
from forms.forms import TransactionForm # <--- Importer le formulaire

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@transactions_bp.route('/ajouter/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_transaction(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Initialiser le formulaire en passant l'ID de l'organisation pour peupler les exercices
    form = TransactionForm(organisation_id=organisation.id)

    # Calculer le montant restant à facturer
    # Soyez précis sur le type de transaction si nécessaire (ex: 'Entrée' ou 'Facture')
    total_billed = sum(t.montant for t in projet.transactions if t.type == 'Entrée') 
    remaining_to_bill = projet.prix_total - total_billed

    # Si le formulaire est soumis et valide (inclut la vérification CSRF)
    if form.validate_on_submit():
        montant = form.montant.data # Récupérer les données depuis form.data

        # --- Validation métier spécifique (montant restant) ---
        # On vérifie si le type est 'Entrée' car une 'Sortie' ne devrait pas être limitée par le prix du projet
        if form.type.data == 'Entrée' and montant > remaining_to_bill:
            # Ajouter l'erreur au champ spécifique du formulaire
            form.montant.errors.append(f"Le montant ({montant} €) dépasse le montant restant à facturer ({remaining_to_bill:.2f} €).")
            # Rendre à nouveau le template avec le formulaire contenant l'erreur
            flash("Erreur de validation, veuillez vérifier les champs.", "danger")
            # Pas besoin de return ici, on continue pour afficher le template à la fin
        
        else: # Si la validation métier passe ou n'est pas applicable (ex: Sortie)
            # --- Gestion de l'exercice comptable ---
            exercice_a_lier = None # Variable pour stocker l'objet Exercice à lier

            # Vérifier si l'utilisateur a choisi de créer un nouvel exercice (via le champ caché et JS)
            if form.creer_nouvel_exercice.data == 'true':
                date_debut_exercice = form.date_debut_exercice.data
                date_fin_exercice = form.date_fin_exercice.data

                # Valider les dates du nouvel exercice
                if not date_debut_exercice or not date_fin_exercice:
                    # Ajouter des erreurs aux champs spécifiques si possible, ou utiliser flash
                    form.date_debut_exercice.errors.append("Date de début requise.")
                    form.date_fin_exercice.errors.append("Date de fin requise.")
                    flash("Veuillez renseigner les dates de début et de fin pour le nouvel exercice.", 'danger')
                elif date_debut_exercice >= date_fin_exercice:
                     form.date_fin_exercice.errors.append("La date de fin doit être postérieure à la date de début.")
                     flash("La date de début de l'exercice doit être antérieure à la date de fin.", 'danger')
                else:
                    # Créer le nouvel exercice
                    try:
                        new_exercice = ExerciceComptable(
                            date_debut=date_debut_exercice, 
                            date_fin=date_fin_exercice, 
                            organisation_id=organisation.id
                            # statut='Ouvert' # Le statut a une valeur par défaut dans le modèle
                        )
                        db.session.add(new_exercice)
                        # Pas besoin de flush/commit ici si on commit tout à la fin
                        exercice_a_lier = new_exercice # Assigner l'objet nouvellement créé
                    except Exception as e:
                         db.session.rollback()
                         flash(f"Erreur lors de la création de l'exercice comptable: {e}", 'danger')
                         # Rendre le template avec l'erreur
                         return render_template('ajouter_transaction.html', projet=projet, form=form, remaining_to_bill=remaining_to_bill)

            else: # Utiliser l'exercice sélectionné dans la liste déroulante
                selected_exercice_id = form.exercice_id.data
                # Vérifier si un exercice valide (non placeholder) a été sélectionné
                if selected_exercice_id and selected_exercice_id != 0: 
                    exercice_a_lier = ExerciceComptable.query.get(selected_exercice_id)
                    if not exercice_a_lier:
                        # Cas où l'ID sélectionné n'existe pas (peu probable mais sécuritaire)
                        flash("L'exercice comptable sélectionné est invalide.", 'danger')
                        form.exercice_id.errors.append("Exercice invalide.")
                else:
                    # Aucun exercice sélectionné et pas de création demandée
                    flash("Veuillez sélectionner un exercice comptable ou en créer un nouveau.", 'danger')
                    form.exercice_id.errors.append("Veuillez sélectionner ou créer un exercice.")

            # --- Création de la transaction (si aucune erreur majeure jusqu'ici) ---
            # Vérifier s'il y a eu des erreurs (validation WTForms + métier + exercice)
            if not form.errors and exercice_a_lier: 
                try:
                    selected_compte_id = form.compte_id.data

                    transaction = Transaction(
                        date=form.date.data,
                        type=form.type.data,
                        montant=montant,
                        description=form.description.data,
                        mode_paiement=form.mode_paiement.data,
                        projet_id=projet_id,
                        organisation_id=organisation.id, # Assigner l'ID directement
                        user_id=user_id, # Assigner l'ID directement
                        exercice=exercice_a_lier, # Lier l'objet ExerciceComptable directement
                        reglement="Non réglée", # Valeur par défaut
                        compte_id=selected_compte_id
                    )
                    
                    db.session.add(transaction)
                    db.session.commit()
                    flash('Transaction ajoutée avec succès!', 'success')
                    # Rediriger vers le détail du projet
                    return redirect(url_for('projets.projet_detail', projet_id=projet_id)) 
                
                except Exception as e:
                    db.session.rollback() # Annuler les changements en cas d'erreur DB
                    flash(f'Erreur lors de l\'ajout de la transaction: {e}', 'danger')
            else:
                 # S'il y a des erreurs (y compris celles ajoutées manuellement comme le montant), 
                 # le template sera rendu à la fin de la fonction avec le formulaire contenant les erreurs.
                 flash("Veuillez corriger les erreurs dans le formulaire.", "warning")


    # Si méthode GET ou si la validation du formulaire a échoué (y compris erreurs métier ajoutées)
    # Le formulaire `form` contient les données soumises (si POST échoué) ou les valeurs par défaut (si GET)
    # et les erreurs de validation.
    return render_template('ajouter_transaction.html', 
                           projet=projet, 
                           form=form, # Passer l'objet formulaire au template
                           remaining_to_bill=remaining_to_bill)


@transactions_bp.route('/modifier_reglement/<int:transaction_id>', methods=['POST'])
@login_required
def modifier_reglement(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Vérifier si l'utilisateur connecté appartient à la même organisation que la transaction
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user or transaction.organisation_id != user.organisation_id:
        flash("Vous n'avez pas la permission de modifier cette transaction.", 'danger')
        # Rediriger vers une page appropriée, peut-être le tableau de bord ou la liste des projets
        return redirect(url_for('projets.projets')) 

    new_reglement = request.form.get('reglement')

    # Valider la nouvelle valeur
    if new_reglement in ["Non réglée", "Réglée", "Partiellement réglée"]:
        try:
            transaction.reglement = new_reglement
            db.session.commit()
            flash(f"Le statut de règlement de la transaction a été mis à jour à '{new_reglement}'.", 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour du statut de règlement: {e}", 'danger')
    else:
        flash("Statut de règlement invalide fourni.", 'danger')

    # Rediriger vers la page de détail du projet associé à la transaction
    return redirect(url_for('projets.projet_detail', projet_id=transaction.projet_id))

