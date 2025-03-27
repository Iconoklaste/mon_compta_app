from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from controllers.db_manager import db
from models import User, Organisation
from werkzeug.security import generate_password_hash, check_password_hash

users_bp = Blueprint('users', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('users.index')) # Redirect to index instead of login
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(mail=email).first()
        if user and user.check_password(password): # Use check_password method
            session['user_id'] = user.id
            return redirect(url_for('users.index'))
        else:
            return "Invalid email or password"
    users = User.query.all()
    return render_template('index.html', users=users)

@users_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('users.index'))

@users_bp.route('/modifier_profil', methods=['GET', 'POST'])
@login_required
def modifier_profil():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.nom = request.form['nom']
        user.prenom = request.form['prenom']
        user.mail = request.form['mail']
        user.telephone = request.form['telephone']
        if request.form['password']:
            user.set_password(request.form['password']) # Use set_password method
        db.session.commit()
        return redirect(url_for('users.index'))

    return render_template('modifier_profil.html', user=user)

@users_bp.route('/ajouter_user', methods=['GET', 'POST'])
def ajouter_user():
    organisations = Organisation.query.all()
    
    # Check if there is already a user in the database
    existing_user = User.query.first()
    if existing_user and 'user_id' not in session:
        return redirect(url_for('users.index'))
    
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        mail = request.form['mail']
        telephone = request.form['telephone']
        password = request.form['password']
        organisation_designation = request.form['organisation']

        # Get the organization object
        organisation = Organisation.query.filter_by(designation=organisation_designation).first()
        if not organisation:
            # Handle the case where the organization doesn't exist
            return "Organisation not found", 400

        new_user = User(nom=nom, prenom=prenom, mail=mail, telephone=telephone, organisation=organisation)
        new_user.set_password(password) # Use set_password method
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('users.index'))

    return render_template('ajouter_user.html', organisations=organisations, user_organisation=None)
