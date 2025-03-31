# c:\wamp\www\mon_compta_app\controllers\whiteboard_controller.py

from flask import Blueprint, render_template, request, jsonify
from controllers.db_manager import db
from models import Whiteboard, Projet
import json

whiteboard_bp = Blueprint('whiteboard', __name__)

@whiteboard_bp.route('/whiteboard/<int:projet_id>')
def whiteboard_view(projet_id):
    # projet = Projet.query.get_or_404(projet_id) # remove this line
    whiteboard = Whiteboard.query.filter_by(projet_id=projet_id).first()

    if whiteboard:
        whiteboard_data = json.loads(whiteboard.data)
    else:
        # Create a new Whiteboard record if one doesn't exist
        whiteboard = Whiteboard(data=json.dumps({"elements": []}), projet_id=projet_id) # add a default value
        db.session.add(whiteboard)
        db.session.commit()
        whiteboard_data = json.loads(whiteboard.data)

    return render_template('whiteboard.html', projet_id=projet_id, whiteboard_data=whiteboard_data)


@whiteboard_bp.route('/save_whiteboard/<int:projet_id>', methods=['POST']) # change the route here
def save_whiteboard(projet_id): # change the function name here
    # projet = Projet.query.get_or_404(projet_id) # remove this line
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
def load(projet_id):
    whiteboard = Whiteboard.query.filter_by(projet_id=projet_id).first()
    if whiteboard:
        return jsonify(json.loads(whiteboard.data))
    else:
        return jsonify({'message': 'Aucune donnée sauvegardée'})
