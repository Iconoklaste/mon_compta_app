# controllers/transactions_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Projet, Transaction, User, ExerciceComptable, Organisation, CompteComptable
from controllers.db_manager import db
# 'date' from datetime might not be needed if form handles defaults
# from datetime import date 
from controllers.users_controller import login_required
from forms.forms import EntreeForm, SortieForm # <--- Importer le formulaire
from utils.ecritures_comptable_util import generer_ecriture_depuis_transaction, generer_ecriture_paiement_client

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@transactions_bp.route('/ajouter_entree/<int:projet_id>', methods=['GET', 'POST'])
@login_required
def ajouter_entree(projet_id):
    """Gère l'ajout d'une transaction d'entrée (Revenu/Facture) pour un projet."""
    projet = Projet.query.get_or_404(projet_id)
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Utiliser EntreeForm
    form = EntreeForm(organisation_id=organisation.id)

    # Calculer le montant restant à facturer (spécifique aux entrées)
    # Note: Assure-toi que le type 'Entrée' correspond bien à ce que tu utilises
    total_billed = sum(t.montant for t in projet.transactions if t.type == 'Entrée')
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

                    transaction = Transaction(
                        date=form.date.data,
                        type='Entrée', # Défini explicitement
                        montant=montant,
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
    user_id = session['user_id']
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
                    return render_template('ajouter_sortie.html', projet=projet, form=form) # Adapter le template

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
                # Le compte_id vient du QuerySelectField (filtré Classe 6)
                selected_compte_id = form.compte_id.data.id # Récupère l'ID de l'objet CompteComptable

                transaction = Transaction(
                    date=form.date.data,
                    type='Sortie', # Défini explicitement
                    montant=montant,
                    description=form.description.data,
                    mode_paiement=form.mode_paiement.data,
                    projet_id=projet_id,
                    organisation_id=organisation.id,
                    user_id=user_id,
                    exercice=exercice_a_lier,
                    reglement="Réglée", # Une dépense est généralement considérée comme réglée lors de la saisie
                    compte_id=selected_compte_id # ID du compte de charge (Classe 6)
                )

                db.session.add(transaction)
                # Flush pour obtenir l'ID de la transaction avant le commit final
                db.session.flush()

                    # Appeler la génération de l'écriture comptable
                ecriture_generee = generer_ecriture_depuis_transaction(transaction, session=db.session)

                if not ecriture_generee:
                    db.session.rollback()
                    flash("Erreur lors de la génération de l'écriture comptable associée.", 'danger')
                    return render_template('ajouter_sortie.html', projet=projet, form=form)

                # Commit final pour enregistrer la Transaction ET l'EcritureComptable
                db.session.commit()
                flash('Dépense ajoutée avec succès!', 'success')
                return redirect(url_for('projets.projet_detail', projet_id=projet_id))

            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de l\'ajout de la dépense: {e}', 'danger')
        else:
            flash("Veuillez corriger les erreurs dans le formulaire.", "warning")

    # Si GET ou validation échouée
    return render_template('ajouter_sortie.html', # Nouveau template
                           projet=projet,
                           form=form)

@transactions_bp.route('/modifier_reglement/<int:transaction_id>', methods=['POST'])
@login_required
def modifier_reglement(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    user_id = session['user_id']
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
            ecriture_paiement_generee = True # Supposer que c'est bon si on n'a pas besoin de générer
            if transaction.type == 'Entrée' and new_reglement == 'Réglée' and old_reglement != 'Réglée':
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
                if transaction.type == 'Entrée' and new_reglement == 'Réglée' and old_reglement != 'Réglée':
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

