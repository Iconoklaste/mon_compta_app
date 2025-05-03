# controllers/transactions_controller.py
from flask import (Blueprint, 
                   render_template, 
                   request, 
                   redirect, 
                   url_for, 
                   flash, 
                   session, 
                   current_app, 
                   send_from_directory, 
                   abort) 
from flask_login import login_required, current_user
from sqlalchemy import func # Import func for sum
from models import Projet, FinancialTransaction, Revenue, Expense, User, ExerciceComptable, Organisation, CompteComptable # Updated imports
from controllers.db_manager import db
import os # Needed for path operations
from werkzeug.utils import secure_filename # To secure filenames
from controllers.users_controller import login_required
from forms.forms import EntreeForm, SortieForm # <--- Importer le formulaire
from utils.ecritures_comptable_util import generer_ecriture_depuis_transaction, generer_ecriture_paiement_client
import logging

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

logger = logging.getLogger(__name__)

@transactions_bp.route('/ajouter_entree/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_entree(projet_id):
    """Gère l'ajout d'une transaction d'entrée (Revenu/Facture) pour un projet."""
    projet = Projet.query.get_or_404(projet_id)
    user_id = current_user.id
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Utiliser EntreeForm
    form = EntreeForm(organisation_id=organisation.id)

    # Calculer le montant restant à facturer (spécifique aux entrées)
# Query directly using Revenue model for accuracy and efficiency
    total_billed = db.session.query(func.sum(Revenue.montant))\
        .filter(Revenue.projet_id == projet_id)\
        .scalar() or 0
    remaining_to_bill = projet.prix_total - total_billed

    if form.validate_on_submit():
        montant = form.montant.data

        # --- Validation métier spécifique (montant restant) ---
        if montant > remaining_to_bill:
            form.montant.errors.append(f"Le montant ({montant} €) dépasse le montant restant à facturer ({remaining_to_bill:.2f} €).")
            flash("Erreur de validation, veuillez vérifier les champs.", "danger")
        else:
            # --- Gestion de l'exercice comptable (identique à ajouter_transaction) ---
            exercice_a_lier = None
            if form.creer_nouvel_exercice.data == 'true':
                # ... (logique de création du nouvel exercice, identique à ajouter_transaction) ...
                # ... (copie le bloc try/except de création d'exercice ici) ...
                date_debut_exercice = form.date_debut_exercice.data
                date_fin_exercice = form.date_fin_exercice.data
                if not date_debut_exercice or not date_fin_exercice:
                    form.date_debut_exercice.errors.append("Date de début requise.")
                    form.date_fin_exercice.errors.append("Date de fin requise.")
                    flash("Veuillez renseigner les dates de début et de fin pour le nouvel exercice.", 'danger')
                elif date_debut_exercice >= date_fin_exercice:
                    form.date_fin_exercice.errors.append("La date de fin doit être postérieure à la date de début.")
                    flash("La date de début de l'exercice doit être antérieure à la date de fin.", 'danger')
                else:
                    try:
                        new_exercice = ExerciceComptable(
                            date_debut=date_debut_exercice,
                            date_fin=date_fin_exercice,
                            organisation_id=organisation.id
                        )
                        db.session.add(new_exercice)
                        exercice_a_lier = new_exercice
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Erreur lors de la création de l'exercice comptable: {e}", 'danger')
                        # Rendre le template avec l'erreur
                        return render_template('ajouter_entree.html', projet=projet, form=form, remaining_to_bill=remaining_to_bill)

            else: # Utiliser l'exercice sélectionné
                selected_exercice_id = form.exercice_id.data
                if selected_exercice_id: # Vérifie si une valeur a été sélectionnée (pas blank)
                    exercice_a_lier = selected_exercice_id
                    if not exercice_a_lier:
                        flash("L'exercice comptable sélectionné est invalide.", 'danger')
                        form.exercice_id.errors.append("Exercice invalide.")
                else: # Aucun exercice sélectionné et pas de création
                    flash("Veuillez sélectionner un exercice comptable ou en créer un nouveau.", 'danger')
                    form.exercice_id.errors.append("Veuillez sélectionner ou créer un exercice.")

            # --- Création de la transaction (si aucune erreur majeure) ---
            if not form.errors and exercice_a_lier:
                try:
                    # Le compte_id vient du QuerySelectField (filtré Classe 7)
                    selected_compte_id = form.compte_id.data.id # Récupère l'ID de l'objet CompteComptable

                    transaction = Revenue(
                        date=form.date.data,
                        montant=montant, # type='revenue' is handled by polymorphism
                        description=form.description.data,
                        mode_paiement=form.mode_paiement.data,
                        projet_id=projet_id,
                        organisation_id=organisation.id,
                        user_id=user_id,
                        exercice=exercice_a_lier,
                        reglement="Non réglée",
                        compte_id=selected_compte_id # ID du compte de produit (Classe 7)
                    )

                    db.session.add(transaction)
                    # Flush pour obtenir l'ID de la transaction avant le commit final
                    db.session.flush()

                    # Appeler la génération de l'écriture comptable
                    # La fonction ajoute l'écriture à la session mais ne commit pas
                    ecriture_generee = generer_ecriture_depuis_transaction(transaction, session=db.session)

                    if not ecriture_generee:
                        # Si la génération échoue (erreur logguée dans l'utilitaire),
                        # on annule tout et on affiche une erreur.
                        db.session.rollback()
                        flash("Erreur lors de la génération de l'écriture comptable associée.", 'danger')
                        # Rendre à nouveau le template avec le formulaire
                        return render_template('ajouter_entree.html', projet=projet, form=form, remaining_to_bill=remaining_to_bill)

                    # Commit final pour enregistrer la Transaction ET l'EcritureComptable
                    db.session.commit()
                    flash('Entrée ajoutée avec succès et écriture comptable générée avec succès!', 'success')
                    return redirect(url_for('projets.projet_detail', projet_id=projet_id))

                except Exception as e:
                    db.session.rollback()
                    flash(f'Erreur lors de l\'ajout de l\'entrée ou de son écriture comptable: {e}', 'danger')
            else:
                flash("Veuillez corriger les erreurs dans le formulaire.", "warning")

    # Si GET ou validation échouée
    return render_template('ajouter_entree.html', # Nouveau template
                           projet=projet,
                           form=form,
                           remaining_to_bill=remaining_to_bill)


@transactions_bp.route('/ajouter_sortie/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_sortie(projet_id):
    """Gère l'ajout d'une transaction de sortie (Dépense) pour un projet."""
    projet = Projet.query.get_or_404(projet_id)
    user_id = current_user.id
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Utiliser SortieForm
    form = SortieForm(organisation_id=organisation.id)

    # Pas de calcul de montant restant pour les sorties

    if form.validate_on_submit():
        montant = form.montant.data

        # Pas de validation métier spécifique au montant restant ici

        # --- Gestion de l'exercice comptable (identique à ajouter_transaction/ajouter_entree) ---
        exercice_a_lier = None
        if form.creer_nouvel_exercice.data == 'true':
            date_debut_exercice = form.date_debut_exercice.data
            date_fin_exercice = form.date_fin_exercice.data
            if not date_debut_exercice or not date_fin_exercice:
                form.date_debut_exercice.errors.append("Date de début requise.")
                form.date_fin_exercice.errors.append("Date de fin requise.")
                flash("Veuillez renseigner les dates de début et de fin pour le nouvel exercice.", 'danger')
            elif date_debut_exercice >= date_fin_exercice:
                form.date_fin_exercice.errors.append("La date de fin doit être postérieure à la date de début.")
                flash("La date de début de l'exercice doit être antérieure à la date de fin.", 'danger')
            else:
                try:
                    new_exercice = ExerciceComptable(
                        date_debut=date_debut_exercice,
                        date_fin=date_fin_exercice,
                        organisation_id=organisation.id
                    )
                    # Important: Ne pas ajouter à la session ici, on le fera avec la transaction
                    # db.session.add(new_exercice)
                    exercice_a_lier = new_exercice
                    logger.info(f"Nouvel exercice prêt à être lié: {new_exercice.date_debut} - {new_exercice.date_fin}")
                except Exception as e:
                    # Pas besoin de rollback ici car rien n'a été ajouté à la session
                    # db.session.rollback()
                    flash(f"Erreur lors de la préparation du nouvel exercice: {e}", 'danger')
                    logger.error(f"Erreur préparation exercice: {e}", exc_info=True)
                    # Rendre le template avec l'erreur
                    return render_template('ajouter_sortie.html', projet=projet, form=form) # Adapter le template

        else: # Utiliser l'exercice sélectionné
            selected_exercice_obj = form.exercice_id.data # Ceci est l'objet ExerciceComptable
            if selected_exercice_obj: # Vérifie si un objet a été sélectionné
                exercice_a_lier = selected_exercice_obj
                logger.info(f"Exercice sélectionné: ID {exercice_a_lier.id}")
            else: # Aucun exercice sélectionné et pas de création
                flash("Veuillez sélectionner un exercice comptable ou en créer un nouveau.", 'danger')
                form.exercice_id.errors.append("Veuillez sélectionner ou créer un exercice.")
                logger.warning("Aucun exercice sélectionné ou créé.")

        # --- Création de la transaction (si aucune erreur majeure) ---
        if not form.errors and exercice_a_lier:
            try:
                # Le compte_id vient du QuerySelectField (filtré Classe 6)
                selected_compte_id = form.compte_id.data.id # Récupère l'ID de l'objet CompteComptable

                transaction = Expense(
                    date=form.date.data,
                    montant=montant, # type='expense' is handled by polymorphism
                    description=form.description.data,
                    mode_paiement=form.mode_paiement.data,
                    projet_id=projet_id,
                    organisation_id=organisation.id,
                    user_id=user_id,
                    # Si c'est un nouvel exercice, il sera ajouté à la session via la relation
                    # Si c'est un exercice existant, SQLAlchemy gère la liaison
                    exercice=exercice_a_lier,
                    reglement="Réglée", # Une dépense est généralement considérée comme réglée lors de la saisie
                    compte_id=selected_compte_id # ID du compte de charge (Classe 6)
                )

                # --- Handle Attachment Upload (Save to Filesystem) ---
                file = form.attachment.data
                saved_filename = None # Pour rollback potentiel
                if file:
                    try:
                        # Generate a secure filename
                        filename = secure_filename(file.filename)
                        # Consider adding uniqueness to prevent overwrites
                        # import uuid; filename = f"{uuid.uuid4()}_{filename}"
                        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        logger.info(f"Tentative de sauvegarde du fichier '{filename}' vers '{save_path}'")
                        file.save(save_path)
                        transaction.attachment_filename = filename # Store the secure filename
                        transaction.attachment_mimetype = file.mimetype
                        saved_filename = save_path # Keep track for potential rollback
                        logger.info(f"Fichier '{filename}' sauvegardé avec succès.")
                    except Exception as e:
                        # Ne pas bloquer la création de la dépense, mais logger et flasher l'erreur
                        flash(f"Erreur lors de l'enregistrement de la pièce jointe : {e}. La dépense sera créée sans pièce jointe.", "warning")
                        logger.error(f"Erreur sauvegarde pièce jointe: {e}", exc_info=True)
                        transaction.attachment_filename = None # Assurer qu'aucun nom de fichier n'est enregistré
                        transaction.attachment_mimetype = None
                # --- End Handle Attachment ---

                db.session.add(transaction)
                # Flush pour obtenir l'ID de la transaction avant le commit final
                db.session.flush()
                logger.info(f"Transaction Expense (pré-commit ID: {transaction.id}) ajoutée à la session.")

                # Appeler la génération de l'écriture comptable
                ecriture_generee = generer_ecriture_depuis_transaction(transaction, session=db.session)

                if not ecriture_generee:
                    db.session.rollback()
                    # Si on a sauvegardé un fichier, essayer de le supprimer
                    if saved_filename and os.path.exists(saved_filename):
                        try:
                            os.remove(saved_filename)
                            logger.info(f"Fichier '{saved_filename}' supprimé suite à rollback.")
                        except Exception as rm_err:
                            logger.error(f"Erreur lors de la suppression du fichier '{saved_filename}' après rollback: {rm_err}")
                    flash("Erreur lors de la génération de l'écriture comptable associée. La dépense n'a pas été ajoutée.", 'danger')
                    logger.error("Échec de generer_ecriture_depuis_transaction, rollback effectué.")
                    return render_template('ajouter_sortie.html', projet=projet, form=form)

                # Commit final pour enregistrer la Transaction ET l'EcritureComptable
                db.session.commit()
                flash('Dépense ajoutée avec succès et écriture comptable générée !', 'success')
                logger.info(f"Transaction Expense ID {transaction.id} et écriture associée commitées.")
                return redirect(url_for('projets.projet_detail', projet_id=projet_id))

            except Exception as e:
                db.session.rollback()
                 # Si on a sauvegardé un fichier, essayer de le supprimer
                if saved_filename and os.path.exists(saved_filename):
                    try:
                        os.remove(saved_filename)
                        logger.info(f"Fichier '{saved_filename}' supprimé suite à rollback (exception générale).")
                    except Exception as rm_err:
                        logger.error(f"Erreur lors de la suppression du fichier '{saved_filename}' après rollback (exception générale): {rm_err}")
                flash(f'Erreur lors de l\'ajout de la dépense: {e}', 'danger')
                logger.error(f"Erreur lors de l'ajout de la dépense: {e}", exc_info=True)
        else:
            flash("Veuillez corriger les erreurs dans le formulaire.", "warning")
            logger.warning(f"Échec validation formulaire ajouter_sortie: {form.errors}")

    # Si GET ou validation échouée
    return render_template('ajouter_sortie.html', # Nouveau template
                           projet=projet,
                           form=form)

@transactions_bp.route('/modifier_reglement/<int:transaction_id>', methods=['POST'])
@login_required
def modifier_reglement(transaction_id):
    transaction = FinancialTransaction.query.get_or_404(transaction_id)

    user_id = current_user.id
    user = User.query.get(user_id)
    if not user or transaction.organisation_id != user.organisation_id:
        flash("Vous n'avez pas la permission de modifier cette transaction.", 'danger')
        # Rediriger vers la page projet ou une page d'erreur appropriée
        return redirect(url_for('projets.projet_detail', projet_id=transaction.projet_id) if transaction.projet_id else url_for('projets.projets'))


    new_reglement = request.form.get('reglement')
    old_reglement = transaction.reglement # Sauvegarder l'ancien statut

    if new_reglement in ["Non réglée", "Réglée", "Partiellement réglée"]:
        try:
            # Mettre à jour le statut de la transaction
            transaction.reglement = new_reglement

            # --- AJOUT : Générer l'écriture de paiement si nécessaire ---
            ecriture_paiement_generee = True # Assume success if generation is not needed
            # Check if it's a Revenue instance being marked as 'Réglée' for the first time
            if isinstance(transaction, Revenue) and new_reglement == 'Réglée' and old_reglement != 'Réglée':
                # Appeler la fonction de génération de l'écriture de paiement
                # Elle vérifie les doublons et ajoute à la session si nécessaire
                resultat_generation = generer_ecriture_paiement_client(transaction, session=db.session)

                if resultat_generation is None:
                    # La génération a échoué (erreur logguée dans l'utilitaire)
                    ecriture_paiement_generee = False # Marquer comme échoué

            if ecriture_paiement_generee:
                # Si la génération a réussi (ou n'était pas nécessaire), on commit
                db.session.commit()
                flash(f"Le statut de règlement a été mis à jour à '{new_reglement}'.", 'success')
                if isinstance(transaction, Revenue) and new_reglement == 'Réglée' and old_reglement != 'Réglée':
                     flash("L'écriture comptable de paiement a été générée.", 'info')
            else:
                # Si la génération de l'écriture de paiement a échoué
                db.session.rollback() # Annuler la mise à jour du statut aussi
                flash("Erreur lors de la génération de l'écriture comptable de paiement. Le statut n'a pas été mis à jour.", 'danger')
            # --- FIN AJOUT ---

        except Exception as e:
            db.session.rollback()
            # Logguer l'erreur e
            flash(f"Erreur lors de la mise à jour du statut ou de la génération de l'écriture: {e}", 'danger')
    else:
        flash("Statut de règlement invalide fourni.", 'danger')

    # Rediriger vers la page de détail du projet
    return redirect(url_for('projets.projet_detail', projet_id=transaction.projet_id))

@transactions_bp.route('/attachments/<int:transaction_id>')
@login_required
def download_attachment(transaction_id):
    """Serves the attachment file for a given transaction."""
    # Use joinedload to potentially fetch related data efficiently if needed later
    transaction = FinancialTransaction.query.options(
        # db.joinedload(FinancialTransaction.organisation) # Example if needed
    ).get_or_404(transaction_id)
    user = current_user

    # Security Check: Ensure the transaction is an Expense and belongs to the user's org
    if not isinstance(transaction, Expense) or transaction.organisation_id != user.organisation_id:
        logger.warning(f"User {user.id} attempted to access attachment for transaction {transaction_id} without permission.")
        abort(403) # Forbidden

    if not transaction.attachment_filename:
        logger.warning(f"Attachment requested for transaction {transaction_id}, but none exists.")
        abort(404) # Not Found

    try:
        logger.info(f"Serving attachment '{transaction.attachment_filename}' for transaction {transaction_id}")
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            transaction.attachment_filename,
            as_attachment=False # Set to True to force download, False to display inline if possible
        )
    except FileNotFoundError:
         logger.error(f"Attachment file not found on server: {transaction.attachment_filename} for transaction {transaction_id}")
         abort(404)
    except Exception as e:
        logger.error(f"Error serving attachment for transaction {transaction_id}: {e}", exc_info=True)
        abort(500)

# --- NOUVELLE FONCTION : Visualiser la pièce jointe ---
@transactions_bp.route('/view_attachment/<int:transaction_id>')
@login_required
def view_attachment(transaction_id):
    """Sert la pièce jointe pour affichage inline dans le navigateur."""
    transaction = FinancialTransaction.query.get_or_404(transaction_id)
    user = current_user

    # Vérification de sécurité : L'utilisateur appartient à l'organisation de la transaction ?
    # Et est-ce bien une dépense (Expense) ?
    if not user or transaction.organisation_id != user.organisation_id:
        logger.warning(f"User {user.id} attempted to view attachment for transaction {transaction_id} without permission (wrong org).")
        abort(403) # Interdit

    if not isinstance(transaction, Expense):
        logger.warning(f"User {user.id} attempted to view attachment for non-expense transaction {transaction_id}.")
        abort(403) # Interdit (ou 404 si on préfère cacher l'existence)

    if not transaction.attachment_filename:
        logger.warning(f"Attachment view requested for transaction {transaction_id}, but none exists.")
        abort(404) # Non trouvé

    try:
        logger.info(f"Serving attachment '{transaction.attachment_filename}' for inline view (transaction {transaction_id})")
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            transaction.attachment_filename,
            as_attachment=False # Important: Tente d'afficher inline
        )
    except FileNotFoundError:
         logger.error(f"Attachment file not found on server: {transaction.attachment_filename} for transaction {transaction_id}")
         abort(404)
    except Exception as e:
        logger.error(f"Error serving attachment for transaction {transaction_id}: {e}", exc_info=True)
        abort(500)