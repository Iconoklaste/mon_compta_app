# c:\wamp\www\mon_compta_app\controllers\compta_controller.py

from flask import Blueprint, render_template, url_for, redirect, session
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Client, User

compta_bp = Blueprint('compta', __name__, url_prefix='/compta')

@compta_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('users.logout'))
    clients = Client.query.all()
    return render_template('compta/compta_index.html', clients=clients)
