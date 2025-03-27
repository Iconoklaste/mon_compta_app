# controllers/users_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, Organisation
from controllers.db_manager import db
from werkzeug.security import check_password_hash
from functools import wraps

users_bp = Blueprint('users', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('users.login'))
        return f(*args, **kwargs)
    return decorated_function


@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(mail=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('projets.projets'))
        else:
            return "Invalid email or password", 401
    users = User.query.all()
    return render_template('index.html', users=users)



@users_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('users.index'))

@users_bp.route('/ajouter_user', methods=['GET', 'POST'])
def ajouter_user():
    organisations = Organisation.query.all()
    user_organisation = Organisation.query.first()
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        mail = request.form['mail']
        telephone = request.form['telephone']
        password = request.form['password']
        organisation_designation = request.form['organisation']

        organisation = Organisation.query.filter_by(designation=organisation_designation).first()
        if not organisation:
            return "Organisation not found", 400

        new_user = User(nom=nom, prenom=prenom, mail=mail, telephone=telephone, organisation=organisation)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('users.index'))

    return render_template('ajouter_user.html', organisations=organisations, user_organisation=user_organisation)

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
            user.set_password(request.form['password'])
        db.session.commit()
        return redirect(url_for('users.index'))

    return render_template('modifier_profil.html', user=user)

@users_bp.route('/')
@login_required
def index():
    organisations = Organisation.query.all()
    users = User.query.all()
    return render_template('index.html', organisations=organisations, users=users)
