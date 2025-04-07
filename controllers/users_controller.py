from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from controllers.db_manager import db
from models import User, Organisation
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import LoginForm, ModifierProfilForm, AjouterUserForm

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
        user = User.query.filter_by(mail=form.email.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Connexion réussie!', 'success')
            return redirect(url_for('projets.projets'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
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
    flash('Vous êtes maintenant déconnecté.', 'success')
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