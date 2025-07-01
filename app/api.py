from flask import Blueprint, request, jsonify
from utils.utils import event_to_dict
from app.db_operations import (
    create_user, authenticate_user, create_event
)
from app.db_operations import *

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

@api.route('/events/<int:event_id>', methods=['GET'])
def api_get_event(event_id):
    event = Evento.query.get(event_id)
    if not event:
        return jsonify({'error': 'Evento não encontrado.'}), 404
    return jsonify(event_to_dict(event)), 200

@api.route('/events', methods=['GET'])
def api_get_events():
    limit = request.args.get('limit', default=10, type=int)
    events = Evento.query.order_by(Evento.data_inicio).limit(limit).all()
    return jsonify([event_to_dict(event) for event in events]), 200

@api.route('/convidados', methods=['GET'])
def api_get_convidados():
    convidados = Convidados.query.all()
    return jsonify([{
        'id_convidado': c.id_convidado,
        'nome': c.nome,
        'bio': c.bio,
        'foto': c.foto
    } for c in convidados]), 200

@api.route('/convidados/<int:convidado_id>', methods=['GET'])
def api_get_convidado(convidado_id):
    convidado = Convidados.query.get(convidado_id)
    if not convidado:
        return jsonify({'error': 'Convidado não encontrado.'}), 404
    return jsonify({
        'id_convidado': convidado.id_convidado,
        'nome': convidado.nome,
        'bio': convidado.bio,
        'foto': convidado.foto
    }), 200

@api.route('/convidados', methods=['POST'])
def api_create_convidado():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400

    nome = data.get('nome')
    bio = data.get('bio')
    foto = data.get('foto')

    if not nome:
        return jsonify({'error': 'Nome é obrigatório.'}), 400

    try:
        convidado = create_convidado(nome, bio, foto)
        return jsonify({
            'success': True,
            'id_convidado': convidado.id_convidado
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/users', methods=['GET'])
def api_get_users():
    users = Usuario.query.all()
    return jsonify([{
        'id_usuario': u.id_usuario,
        'nome': u.nome,
        'email': u.email,
        'tipo': u.tipo.nome
    } for u in users]), 200

@api.route('/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404
    return jsonify({
        'id_usuario': user.id_usuario,
        'nome': user.nome,
        'email': user.email,
        'tipo': user.tipo.nome
    }), 200

@api.route('/users/<int:user_id>/events', methods=['GET'])
def api_get_user_events(user_id):
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404
    inscricoes = InscricaoEvento.query.filter_by(id_usuario=user_id).all()
    events = [event_to_dict(inscricao.evento) for inscricao in inscricoes]
    return jsonify(events), 200

