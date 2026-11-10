# c:\wamp\www\mon_compta_app\controllers\whiteboard_controller.py

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import current_user
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Whiteboard, Projet
import json

whiteboard_bp = Blueprint('whiteboard', __name__)


def _projet_de_mon_organisation(projet_id):
    """Renvoie le projet s'il appartient à l'organisation de l'utilisateur connecté, sinon 404."""
    projet = Projet.query.get_or_404(projet_id)
    if projet.organisation_id != current_user.organisation_id:
        abort(404)
    return projet


@whiteboard_bp.route('/whiteboard/<int:projet_id>')
@login_required
def whiteboard_view(projet_id):
    projet = _projet_de_mon_organisation(projet_id)
    return render_template('whiteboard.html', projet=projet, projet_id=projet_id)


@whiteboard_bp.route('/whiteboard-test/<int:projet_id>')
@login_required
def whiteboard_test_view(projet_id):
    projet = _projet_de_mon_organisation(projet_id)
    return render_template('test-pen.html', projet=projet, projet_id=projet_id)


@whiteboard_bp.route('/save_whiteboard/<int:projet_id>', methods=['POST'])
@login_required
def save_whiteboard(projet_id):
    _projet_de_mon_organisation(projet_id)
    data = request.get_json()
    data_json = json.dumps(data)

    whiteboard = Whiteboard.query.filter_by(projet_id=projet_id).first()

    if whiteboard:
        whiteboard.data = data_json
    else:
        whiteboard = Whiteboard(data=data_json, projet_id=projet_id)
        db.session.add(whiteboard)

    db.session.commit()
    return jsonify({'message': 'Whiteboard sauvegardé'})

@whiteboard_bp.route('/load/<int:projet_id>', methods=['GET'])
@login_required
def load(projet_id):
    _projet_de_mon_organisation(projet_id)
    whiteboard = Whiteboard.query.filter_by(projet_id=projet_id).first()
    if whiteboard:
        return jsonify(whiteboard_data=json.loads(whiteboard.data)) # change the response here
    else:
        return jsonify({'whiteboard_data': None}) # change the response here
