from flask import Blueprint, request, jsonify
from utils.utils import event_to_dict
from app.db_operations import (
    create_user, authenticate_user, create_event
)

api = Blueprint('api', __name__)

@api.route('/sign_up', methods=['POST'])
def api_sign_up():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    if not (nome and email and senha):
        return jsonify({'error': 'Nome, email e senha são obrigatórios.'}), 400

    user, error = create_user(nome, email, senha)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'id_usuario': user.id_usuario}), 201

@api.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    email = data.get('email')
    senha = data.get('senha')
    if not (email and senha):
        return jsonify({'error': 'Email e senha são obrigatórios.'}), 400

    user = authenticate_user(email, senha)
    if user:
        user_json = {
            'id_usuario': user.id_usuario,
            'nome': user.nome,
            'email': user.email,
            'tipo': user.tipo.nome
        }
        return jsonify({'success': True, 'user': user_json}), 200
    return jsonify({'error': 'Credenciais inválidas.'}), 401

@api.route('/events', methods=['POST'])
def api_create_event():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400

    try:
        ev = create_event(data)
        return jsonify({'success': True, 'id_evento': ev.id_evento}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400