from flask import Blueprint, render_template, redirect, session, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, Client, FinancialTransaction, Revenue, Expense, Organisation, Projet, EquipeMembre,  Phase, Jalon # Updated imports
from datetime import date
from forms.forms import ProjetForm, ClientForm, EquipeMembreForm

projets_bp = Blueprint('projets', __name__)

@projets_bp.route('/projets')
@login_required
def projets():
    user_id = current_user.id
    projets = Projet.query.filter_by(user_id=user_id).all()
    return render_template('projets.html',
                           projets=projets,
                           current_page='Projets')


@projets_bp.route('/projet/<int:projet_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    form = ProjetForm(obj=projet)

    if form.validate_on_submit():
        projet.nom = form.nom.data
        projet.client_id = form.client_id.data
        projet.date_debut = form.date_debut.data
        projet.date_fin = form.date_fin.data
        projet.statut = form.statut.data
        projet.prix_total = form.prix_total.data

        db.session.commit()
        flash('Projet modifié avec succès!', 'success')
        return redirect(url_for('projets.projet_detail', projet_id=projet.id))
    return render_template('projet_edit.html', projet=projet, form=form)


@projets_bp.route('/projet/<int:projet_id>/supprimer', methods=['POST'])
@login_required
def supprimer_projet(projet_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        # Handle CSRF error (e.g., return an error response)
        return "CSRF token validation failed", 400
    projet = Projet.query.get_or_404(projet_id)
    # Delete related transactions first (if necessary)
    for transaction in projet.transactions:
        db.session.delete(transaction)
    db.session.delete(projet)
    db.session.commit()
    flash('Projet supprimé avec succès!', 'success')
    return redirect(url_for('projets.projets'))

@projets_bp.route('/<int:projet_id>')
@login_required
def projet_detail(projet_id):
    # Charger le projet et précharger les membres et leurs utilisateurs associés si possible
    projet = Projet.query.options(
        joinedload(Projet.membres).joinedload(EquipeMembre.user)
    ).get_or_404(projet_id)

    # Vérifier l'accès (si l'utilisateur fait partie de l'organisation du projet)
    user_id = current_user.id
    user = User.query.get(user_id)
    if not user or projet.organisation_id != user.organisation_id:
         flash("Accès non autorisé à ce projet.", "danger")
         return redirect(url_for('projets.projets')) # Ou une autre page appropriée

    # Le reste de ta logique existante pour projet_detail
    client = Client.query.get(projet.client_id) if projet.client_id else None # Gérer le cas où client_id est null
    # Fetch all transactions (Revenue/Expense) for the project
    transactions = FinancialTransaction.query.filter_by(projet_id=projet_id).order_by(FinancialTransaction.date.desc()).all()

    # Recalculate phase progress
    for phase in projet.phases:
        total_jalons = len(phase.jalons)
        completed_jalons = sum(1 for j in phase.jalons if j.atteint)
        phase.progress = (completed_jalons / total_jalons) * 100 if total_jalons > 0 else 0

    # Recalculate overall project progress
    total_phases = len(projet.phases)
    if total_phases > 0:
        projet.progress = sum(phase.progress for phase in projet.phases) / total_phases
    else:
        projet.progress = 0

    # Pas besoin de db.session.commit() ici si on ne fait que lire et calculer

    # Calculate remaining to bill
    total_billed = db.session.query(func.sum(Revenue.montant)).filter(Revenue.projet_id == projet_id).scalar() or 0
    # total_paid = db.session.query(func.sum(Transaction.montant)).filter(Transaction.projet_id == projet_id, Transaction.type == 'Paiement').scalar() or 0 # Type Paiement n'existe plus ?
    # Si tu veux le total payé, il faut se baser sur le statut 'Réglée' des transactions 'Entrée'
# Query Revenue directly
    total_paid = db.session.query(func.sum(Revenue.montant)).filter(
        Revenue.projet_id == projet_id,
        Revenue.reglement == 'Réglée'
    ).scalar() or 0
    # Le calcul du reste à facturer doit peut-être être revu selon ta logique exacte
    # Reste à facturer = Prix total - Total déjà facturé (Entrée)
    remaining_to_bill = projet.prix_total - total_billed
    # Solde dû par le client = Total facturé (Entrée) - Total payé (Entrée réglée)
    due_balance = total_billed - total_paid

    # --- NOUVEAU : Préparer le formulaire d'ajout de membre ---
    membre_form = EquipeMembreForm()
    # Récupérer les utilisateurs de l'organisation une seule fois
    users_in_org = User.query.filter_by(organisation_id=user.organisation_id).order_by(User.nom).all()

    # Pré-remplir les choix du formulaire
    membre_form.user_id.choices = [(u.id, u.nom_complet) for u in users_in_org]
    membre_form.user_id.choices.insert(0, ('', '--- Sélectionner un utilisateur existant (Optionnel) ---'))

    # Préparer les données utilisateur pour JavaScript (sélection d'infos utiles)
    users_data_for_js = {
        u.id: {'nom': u.nom, 'email': u.mail}
        for u in users_in_org
    }
    # --- NOUVEAU : Récupérer les membres (déjà chargés avec joinedload) ---
    membres_equipe = projet.membres 

    # --- NOUVEAU : Préparer les données pour le Gantt ---
    phases_data = []
    for phase in projet.phases: # Utilise .all() si lazy='dynamic'
        phases_data.append({
            'id': phase.id,
            'nom': phase.nom,
            # Formate les dates en ISO (YYYY-MM-DD) pour Frappe Gantt
            'date_debut': phase.date_debut.strftime('%Y-%m-%d') if phase.date_debut else None,
            'date_fin': phase.date_fin.strftime('%Y-%m-%d') if phase.date_fin else None,
            'progress': phase.progress,
            # Ajoute d'autres champs si nécessaire pour le Gantt ou JS
        })

    jalons_data = []
    # Attention: projet.jalons n'existe peut-être pas directement.
    # Il faut peut-être itérer sur les phases puis les jalons de chaque phase.
    all_jalons = []
    for phase in projet.phases:
        all_jalons.extend(phase.jalons) # Utilise .all() si lazy='dynamic'

    for jalon in all_jalons:
         # Assure-toi que tes jalons ont une date_echeance ou similaire
         date_echeance_str = None
         if hasattr(jalon, 'date_echeance') and jalon.date_echeance:
             date_echeance_str = jalon.date_echeance.strftime('%Y-%m-%d')
         elif hasattr(jalon, 'date_fin') and jalon.date_fin: # Fallback sur date_fin si pas d'échéance
              date_echeance_str = jalon.date_fin.strftime('%Y-%m-%d')

         jalons_data.append({
            'id': jalon.id,
            'nom': jalon.nom,
            'date_echeance': date_echeance_str, # Utilise la date formatée
            'atteint': jalon.atteint,
            'phase_id': jalon.phase_id
            # Ajoute d'autres champs si nécessaire
         })

    return render_template(
        'projet_detail.html',
        projet=projet,
        client=client,
        transactions=transactions,
        remaining_to_bill=remaining_to_bill,
        due_balance=due_balance, # Ajout du solde dû
        membres_equipe=membres_equipe, # <-- Passer les membres au template
        membre_form=membre_form, # <-- Passer le formulaire au template
        users_data_json=users_data_for_js,
        phases_data=phases_data,
        jalons_data=jalons_data,
    )

@projets_bp.route('/ajouter_projet', methods=['GET', 'POST'])
@login_required
def ajouter_projet():
    form = ProjetForm()
    user_id = current_user.id
    user = User.query.get(user_id)
    if not user:
        abort(404)
    form.client_id.choices = [(client.id, client.nom) for client in Client.query.all()]
    form.statut.choices = [("En attente", "En attente"), ("En cours", "En cours"), ("Terminé", "Terminé"), ("Annulé", "Annulé")]

    if form.validate_on_submit():
        try:
            validate_csrf(form.csrf_token.data)
        except Exception as e:
            flash("Erreur CSRF", 'danger')
            return redirect(url_for('projets.ajouter_projet'))

        organisation = user.organisation # Use the user's organisation
        if not organisation:
            # This case should ideally not happen if user setup is correct, but good to check
            flash("Impossible de déterminer l'organisation de l'utilisateur.", 'danger')
            return redirect(url_for('projets.projets')) # Or another appropriate page


        client = Client.query.get(form.client_id.data)
        if not client:
            flash("Client non trouvé.", 'danger')
            return redirect(url_for('projets.ajouter_projet'))

        nouveau_projet = Projet(
            nom=form.nom.data,
            date_debut=form.date_debut.data,
            date_fin=form.date_fin.data,
            statut=form.statut.data,
            prix_total=form.prix_total.data,
            organisation=organisation,
            user=user,
            client=client
        )
        db.session.add(nouveau_projet)
        db.session.commit()
        flash('Projet ajouté avec succès!', 'success')
        return redirect(url_for('projets.projets'))

    return render_template('ajouter_projet.html', clients=Client.query.all(), form=form, status_options=["En attente", "En cours", "Terminé", "Annulé"])

@projets_bp.route('/<int:projet_id>/ajouter_membre', methods=['POST'])
@login_required
def ajouter_membre_equipe(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    user_id = current_user.id
    user = User.query.get(user_id)

    # Vérifier les permissions (l'utilisateur appartient à l'organisation du projet)
    if not user or projet.organisation_id != user.organisation_id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for('projets.projets'))

    form = EquipeMembreForm(request.form) # Récupérer les données du formulaire POST
    # Re-populer les choix pour la validation et si on doit ré-afficher le formulaire
    form.user_id.choices = [(u.id, u.nom_complet) for u in User.query.filter_by(organisation_id=user.organisation_id).order_by(User.nom)]
    form.user_id.choices.insert(0, ('', '--- Sélectionner un utilisateur existant (Optionnel) ---'))

    if form.validate_on_submit():
        selected_user_id = form.user_id.data
        email = form.email.data
        nom = form.nom.data
        role_projet = form.role_projet.data

        membre_existant = None
        user_to_link = None

        # 1. Vérifier si un utilisateur existant a été sélectionné
        if selected_user_id:
            user_to_link = User.query.filter_by(id=selected_user_id, organisation_id=user.organisation_id).first()
            if user_to_link:
                # Vérifier si cet utilisateur est déjà membre du projet
                membre_existant = EquipeMembre.query.filter_by(projet_id=projet_id, user_id=user_to_link.id).first()
                # Pré-remplir nom/email si vides, basé sur l'utilisateur sélectionné
                if not nom: nom = user_to_link.nom_complet
                if not email: email = user_to_link.mail
            else:
                flash("Utilisateur sélectionné invalide.", "warning")
                # On ne bloque pas forcément, on continue comme si c'était un membre externe

        # 2. Si pas d'utilisateur sélectionné OU utilisateur invalide, vérifier par email
        if not membre_existant and email:
             membre_existant = EquipeMembre.query.filter_by(projet_id=projet_id, email=email).first()

        # 3. Si le membre existe déjà, afficher une erreur
        if membre_existant:
            flash(f"'{membre_existant.nom}' ({membre_existant.email}) fait déjà partie de l'équipe.", 'warning')
        else:
            # 4. Créer le nouveau membre
            try:
                nouveau_membre = EquipeMembre(
                    nom=nom,
                    email=email,
                    role_projet=role_projet,
                    projet_id=projet_id,
                    user_id=user_to_link.id if user_to_link else None # Lier l'user_id si trouvé et valide
                )
                db.session.add(nouveau_membre)
                db.session.commit()
                flash(f"'{nouveau_membre.nom}' ajouté à l'équipe du projet.", 'success')
            except Exception as e:
                db.session.rollback()
                flash(f"Erreur lors de l'ajout du membre : {e}", 'danger')

        return redirect(url_for('projets.projet_detail', projet_id=projet_id))

    else:
        # Si le formulaire n'est pas valide, afficher les erreurs et rediriger
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", 'danger')
        # Pour réafficher la page détail avec le formulaire en erreur, il faudrait recharger toutes les données...
        # C'est plus simple de juste rediriger pour l'instant, l'utilisateur devra rouvrir le formulaire.
        # Une meilleure approche serait d'utiliser AJAX pour l'ajout.
        flash("Erreur de validation. Veuillez vérifier les informations saisies.", "warning")
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))


# --- NOUVELLE ROUTE : Supprimer un membre de l'équipe ---
@projets_bp.route('/<int:projet_id>/supprimer_membre/<int:membre_id>', methods=['POST'])
@login_required
def supprimer_membre_equipe(projet_id, membre_id):
    # Valider le token CSRF (important pour les actions POST)
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash("Erreur de sécurité (CSRF). Action annulée.", 'danger')
        return redirect(url_for('projets.projet_detail', projet_id=projet_id))

    user_id = current_user.id
    user = User.query.get(user_id)
    membre_a_supprimer = EquipeMembre.query.get_or_404(membre_id)

    # Vérifier les permissions :
    # 1. Le membre appartient bien au projet spécifié
    # 2. L'utilisateur connecté appartient à l'organisation du projet
    if membre_a_supprimer.projet_id != projet_id or not user or membre_a_supprimer.projet.organisation_id != user.organisation_id:
        flash("Action non autorisée ou membre introuvable pour ce projet.", "danger")
        return redirect(url_for('projets.projets'))

    try:
        nom_membre = membre_a_supprimer.nom # Garder le nom pour le message flash
        db.session.delete(membre_a_supprimer)
        db.session.commit()
        flash(f"'{nom_membre}' a été retiré de l'équipe du projet.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du membre : {e}", 'danger')

    return redirect(url_for('projets.projet_detail', projet_id=projet_id))

# --- NOUVELLE ROUTE : Modifier un membre de l'équipe ---
@projets_bp.route('/<int:projet_id>/modifier_membre/<int:membre_id>', methods=['POST'])
@login_required
def modifier_membre_equipe(projet_id, membre_id):
    """
    Gère la modification d'un membre de l'équipe via le formulaire modal.
    """
    projet = Projet.query.get_or_404(projet_id)
    membre = EquipeMembre.query.filter_by(id=membre_id, projet_id=projet.id).first_or_404()
    user_id = current_user.id
    user = User.query.get(user_id)

    # --- Vérification des permissions (cohérent avec les autres routes) ---
    if not user or projet.organisation_id != user.organisation_id:
        flash("Action non autorisée.", "danger")
        # Rediriger vers la liste des projets ou la page d'accueil
        return redirect(url_for('projets.projets'))

    # Instancier le formulaire avec les données POST et l'objet existant
    form = EquipeMembreForm(request.form, obj=membre)

    # --- Peupler les choix d'utilisateurs (important AVANT la validation) ---
    # (Similaire à ajouter_membre_equipe et projet_detail)
    users_in_org = User.query.filter_by(organisation_id=user.organisation_id).order_by(User.nom).all()
    form.user_id.choices = [(u.id, u.nom_complet) for u in users_in_org]
    form.user_id.choices.insert(0, ('', '--- Sélectionner un utilisateur existant (Optionnel) ---'))
    # --------------------------------------------------------------------

    # validate_on_submit() gère la validation ET le CSRF pour les POST standards
    if form.validate_on_submit():
        try:
            # Mettre à jour les champs du membre existant
            membre.nom = form.nom.data
            membre.email = form.email.data # L'email est requis par le formulaire
            membre.role_projet = form.role_projet.data

            # Gérer la liaison utilisateur (similaire à l'ajout)
            selected_user_id = form.user_id.data
            user_to_link = None
            if selected_user_id:
                user_to_link = User.query.filter_by(id=selected_user_id, organisation_id=user.organisation_id).first()
                if user_to_link:
                    membre.user_id = user_to_link.id
                    # Optionnel : Forcer la synchronisation nom/email si lié ?
                    # membre.nom = user_to_link.nom_complet
                    # membre.email = user_to_link.mail
                else:
                    # Si l'ID sélectionné n'est pas valide (ne devrait pas arriver avec le select), on dé-lie
                    membre.user_id = None
                    flash("L'utilisateur interne sélectionné n'a pas été trouvé. Le membre reste externe.", "warning")
            else:
                # Si aucun utilisateur n'est sélectionné, s'assurer que le lien est retiré
                membre.user_id = None

            db.session.commit()
            flash(f"Le membre '{membre.nom}' a été mis à jour avec succès.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour du membre : {e}", "danger")

        return redirect(url_for('projets.projet_detail', projet_id=projet.id))

    else:
        # --- Si la validation échoue ---
        flash("Erreur de validation lors de la modification du membre.", 'danger')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", 'danger')
        # Rediriger vers la page détail. L'utilisateur devra rouvrir le modal.
        return redirect(url_for('projets.projet_detail', projet_id=projet.id))