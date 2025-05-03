from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from controllers.db_manager import db
from models import User, Organisation
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import (LoginForm, 
                         ModifierProfilForm, 
                         AjouterUserForm, 
                         AjouterUserFormDemo, 
                         ChatbotQuestionForm)

from flask_login import login_user, logout_user, login_required, current_user # <-- Importer les fonctions et current_user
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)


@users_bp.route('/', methods=['GET', 'POST'])
def index():
    # --- Vérifier si l'utilisateur est déjà connecté ---
    if current_user.is_authenticated:
        logger.debug(f"Utilisateur ID {current_user.id} déjà connecté, redirection vers /accueil.")
        return redirect(url_for('users.accueil')) # Redirige vers la nouvelle route


    # --- Si l'utilisateur N'EST PAS connecté ---
    # On affiche la page publique (index.html) avec le formulaire de connexion
    form = LoginForm()
    # La variable orga_designation n'est plus utile ici car on ne l'affiche que si l'user est connecté
    # orga_designation = None # On peut supprimer cette ligne

    # --- Traitement du formulaire de connexion (si soumis en POST) ---
    if form.validate_on_submit(): # S'exécute seulement si la méthode est POST et la validation réussit
        email_fourni = form.email.data
        password_fourni = form.password.data
        logger.debug(f"Tentative de connexion pour l'email : {email_fourni}")

        user = User.query.filter_by(mail=email_fourni).first()

        if user:
            logger.debug(f"Utilisateur trouvé : {user.mail} (ID: {user.id})")
            password_check_result = user.check_password(password_fourni)
            logger.debug(f"Résultat de user.check_password() : {password_check_result}")

            if password_check_result:
                # --- Enregistrement des infos en session ---
                login_user(user)
                session['user_prenom'] = user.prenom
                # S'assurer que l'organisation existe avant d'accéder à 'designation'
                orga_designation = user.organisation.designation if user.organisation else "Organisation inconnue"
                session['organisation'] = orga_designation
                # -------------------------------------------
                logger.info(f"Connexion réussie pour l'utilisateur ID: {user.id}, organisation {orga_designation}")
                flash('Connexion réussie!', 'success')
                # Redirige vers la même route ('users.index'), qui affichera maintenant index_user.html
                return redirect(url_for('users.accueil'))
            else:
                logger.warning(f"Mot de passe incorrect pour l'utilisateur : {email_fourni}")
                flash('Email ou mot de passe incorrect.', 'danger')
        else:
            logger.warning(f"Aucun utilisateur trouvé pour l'email : {email_fourni}")
            flash('Email ou mot de passe incorrect.', 'danger')
        # Si la connexion échoue (mauvais email/mdp), on ne fait rien de plus ici,
        # la fonction continuera et réaffichera index.html avec le message flash d'erreur.

    elif request.method == 'POST':
         # Si c'est un POST mais que form.validate_on_submit() est False
         logger.warning(f"Échec de validation du formulaire de connexion : {form.errors}")
         flash('Erreur de validation du formulaire. Vérifiez les champs.', 'warning')

    # --- Affichage de la page publique (index.html) pour une requête GET ---
    # --- ou si la connexion POST a échoué ---
    logger.debug("Utilisateur non connecté ou échec connexion, affichage de index.html (login)")
    # On passe seulement le formulaire à index.html
    return render_template('index.html', forms=form)

@users_bp.route('/accueil') # Nouvelle URL
@login_required # Assure que seul un utilisateur connecté peut y accéder
def accueil():
    """Affiche le tableau de bord de l'utilisateur connecté."""
    user_prenom = current_user.prenom
    organisation = current_user.organisation.designation if current_user.organisation else 'Mon Organisation'
    logger.debug(f"Affichage du tableau de bord /accueil pour l'utilisateur ID {current_user.id}")

    # --- Instancier le formulaire du chatbot ---
    chatbot_form = ChatbotQuestionForm()

    return render_template('index_user.html',
                           user_prenom=user_prenom,
                           organisation=organisation,
                           chatbot_form=chatbot_form,
                           current_page='Accueil')


@users_bp.route('/modifier_profil', methods=['GET', 'POST'])
@login_required
def modifier_profil():
    user_id = current_user.id
    user = User.query.get_or_404(user_id)
    form = ModifierProfilForm(obj=user) # Create an instance of the form

    if form.validate_on_submit():
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.mail = form.mail.data
        user.telephone = form.telephone.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')
        return redirect(url_for('users.accueil')) # Redirect to projets page after update

    return render_template('modifier_profil.html', user=user, form=form) # Pass the form to the template

@users_bp.route('/logout')
def logout():
    """Déconnecte l'utilisateur et nettoie la session."""
    user_id = current_user.id if current_user.is_authenticated else None

    session.pop('mistral_chat_history', None)
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'success')
    if user_id:
        logger.info(f"Utilisateur ID {user_id} déconnecté.")
    return redirect(url_for('users.index'))

@users_bp.route('/ajouter_user', methods=['GET', 'POST'])
def ajouter_user():
    form = AjouterUserForm() # Create an instance of the form

    if form.validate_on_submit():
        # Check if the email already exists
        existing_user = User.query.filter_by(mail=form.mail.data).first()
        if existing_user:
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('ajouter_user.html', form=form)

        # Get the organization object
        organisation = Organisation.query.filter_by(designation=form.organisation.data).first()
        if not organisation:
            flash('Organisation non trouvée.', 'danger')
            return render_template('ajouter_user.html', form=form)

        new_user = User(
            nom=form.nom.data,
            prenom=form.prenom.data,
            mail=form.mail.data,
            telephone=form.telephone.data,
            organisation=organisation
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Utilisateur ajouté avec succès!', 'success')
        return redirect(url_for('users.accueil')) # Redirect to login page after create a user

    return render_template('ajouter_user.html', form=form) # Pass the form to the template

# --- NOUVELLE ROUTE pour l'étape 1 de l'inscription démo ---
@users_bp.route('/creer-compte-demo/etape-1', methods=['GET', 'POST'])
def ajouter_user_demo():
    """Affiche et traite le formulaire d'informations utilisateur (Étape 1)."""
    # Important: Ne pas utiliser @login_required ici, c'est pour les nouveaux utilisateurs
    form = AjouterUserForm()
    # On retire le champ organisation du formulaire pour cette étape
    del form.organisation

    if form.validate_on_submit():
        # Vérification si l'email existe déjà
        existing_user = User.query.filter_by(mail=form.mail.data).first()
        if existing_user:
            flash('Cet email est déjà utilisé. Veuillez vous connecter ou utiliser un autre email.', 'danger')
            # Re-rendre le formulaire avec l'erreur
            return render_template('ajouter_user_demo.html', form=form)

        # Stocker les données utilisateur validées dans la session
        # On ne stocke PAS le mot de passe en clair trop longtemps, mais ici c'est temporaire
        # pour la requête suivante. Assure-toi que ta clé secrète Flask est bien sécurisée.
        session['demo_user_data'] = {
            'nom': form.nom.data,
            'prenom': form.prenom.data,
            'mail': form.mail.data,
            'telephone': form.telephone.data,
            'password': form.password.data # On aura besoin de le hasher plus tard
        }
        flash("Informations utilisateur enregistrées. Passons à l'organisation.", 'info')
        # Rediriger vers l'étape 2 (création de l'organisation)
        return redirect(url_for('organisations.ajouter_organisation_demo'))

    # Si GET ou si validation échoue
    return render_template('ajouter_user_demo.html', form=form)