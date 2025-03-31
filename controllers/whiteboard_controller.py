from flask import Blueprint, render_template, request, jsonify

whiteboard_bp = Blueprint('whiteboard', __name__)

# Stockage temporaire (à remplacer par une base de données)
whiteboard_data = {}

@whiteboard_bp.route('/whiteboard')
def whiteboard():
    return render_template('whiteboard.html')

@whiteboard_bp.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    whiteboard_data['state'] = data
    return jsonify({'message': 'Whiteboard sauvegardé'})

@whiteboard_bp.route('/load', methods=['GET'])
def load():
    if 'state' in whiteboard_data:
        return jsonify(whiteboard_data['state'])
    else:
        return jsonify({'message': 'Aucune donnée sauvegardée'})
