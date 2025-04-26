from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from controllers.db_manager import db
from models import User, Organisation
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import LoginForm, ModifierProfilForm, AjouterUserForm, AjouterUserFormDemo
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez être connecté pour accéder à cette page.', 'danger')
            return redirect(url_for('users.index'))  # Redirect to index (login)
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        email_fourni = form.email.data
        password_fourni = form.password.data
        logger.debug(f"Tentative de connexion pour l'email : {email_fourni}") # Log l'email

        user = User.query.filter_by(mail=email_fourni).first()

        if user:
            logger.debug(f"Utilisateur trouvé : {user.mail} (ID: {user.id})") # Log si l'utilisateur est trouvé
            # --- AJOUT DU PRINT/LOG CRUCIAL ---
            password_check_result = user.check_password(password_fourni)
            logger.debug(f"Résultat de user.check_password() : {password_check_result}")
            # ---------------------------------

            if password_check_result:
                session['user_id'] = user.id
                logger.info(f"Connexion réussie pour l'utilisateur ID: {user.id}") # Log succès
                flash('Connexion réussie!', 'success')
                return redirect(url_for('users.index'))
            else:
                logger.warning(f"Mot de passe incorrect pour l'utilisateur : {email_fourni}") # Log échec mdp
                flash('Email ou mot de passe incorrect.', 'danger')
        else:
            logger.warning(f"Aucun utilisateur trouvé pour l'email : {email_fourni}") # Log utilisateur non trouvé
            flash('Email ou mot de passe incorrect.', 'danger')
    elif request.method == 'POST':
         # Si la validation échoue sur un POST, log les erreurs
         logger.warning(f"Échec de validation du formulaire de connexion : {form.errors}")
         flash('Erreur de validation du formulaire.', 'warning')

    return render_template('index.html', forms=form)

@users_bp.route('/modifier_profil', methods=['GET', 'POST'])
@login_required
def modifier_profil():
    user_id = session['user_id']
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
        return redirect(url_for('projets.projets')) # Redirect to projets page after update

    return render_template('modifier_profil.html', user=user, form=form) # Pass the form to the template

@users_bp.route('/logout')
def logout():
    session.pop('user_id', None)
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
        return redirect(url_for('users.index')) # Redirect to login page after create a user

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