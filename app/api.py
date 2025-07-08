from flask import Blueprint, request, jsonify
from utils.utils import event_to_dict
from app.db_operations import *
from app.helpers import api_requires_login, api_requires_admin, logged_user

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
@api_requires_admin
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

@api.route('/events/<int:event_id>', methods=['PUT'])
@api_requires_admin
def api_update_event(event_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    try:
        update_event(event_id, data)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/events/<int:event_id>', methods=['DELETE'])
@api_requires_admin
def api_delete_event(event_id):
    try:
        delete_event(event_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
@api_requires_admin
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

@api.route('/convidados/<int:convidado_id>', methods=['PUT'])
@api_requires_admin
def api_update_convidado(convidado_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    try:
        update_convidado(convidado_id, data)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/convidados/<int:convidado_id>', methods=['DELETE'])
@api_requires_admin
def api_delete_convidado(convidado_id):
    try:
        delete_convidado(convidado_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/users', methods=['GET'])
@api_requires_admin
def api_get_users():
    users = Usuario.query.all()
    return jsonify([{
        'id_usuario': u.id_usuario,
        'nome': u.nome,
        'email': u.email,
        'tipo': u.tipo.nome
    } for u in users]), 200

@api.route('/users/<int:user_id>', methods=['GET'])
@api_requires_login
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


@api.route('/users/<int:user_id>', methods=['DELETE'])
@api_requires_admin
def api_delete_user(user_id):
    try:
        delete_usuario(user_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api.route('/users/<int:user_id>/events', methods=['GET'])
def api_get_user_events(user_id):
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404
    inscricoes = InscricaoEvento.query.filter_by(id_usuario=user_id).all()
    events = [event_to_dict(inscricao.evento) for inscricao in inscricoes]
    return jsonify(events), 200

@api.route('/events/<int:event_id>/register', methods=['POST'])
@api_requires_login
def api_register_event(event_id):
    user = logged_user()
    success, error = register_user_in_event(user.id_usuario, event_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': error or 'Erro ao se inscrever no evento.'}), 400

@api.route('/events/<int:event_id>/cancel', methods=['POST'])
@api_requires_login
def api_cancel_event_registration(event_id):
    user = logged_user()
    success, error = cancel_inscricao(user.id_usuario, event_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': error or 'Não foi possível cancelar a inscrição.'}), 400

@api.route('/events/<int:event_id>/activities', methods=['GET'])
def api_get_event_activities(event_id):
    atividades = get_atividades_by_event(event_id)
    return jsonify([{'id_atividade': a.id_atividade, 'titulo': a.titulo, 'descricao': a.descricao, 'data_hora': a.data_hora, 'duracao_minutos': a.duracao_minutos, 'tipo': a.tipo.nome} for a in atividades]), 200

@api.route('/activities/<int:activity_id>', methods=['GET'])
def api_get_activity(activity_id):
    atividade = Atividade.query.get(activity_id)
    if not atividade:
        return jsonify({'error': 'Atividade não encontrada.'}), 404
    return jsonify({'id_atividade': atividade.id_atividade, 'titulo': atividade.titulo, 'descricao': atividade.descricao, 'data_hora': atividade.data_hora, 'duracao_minutos': atividade.duracao_minutos, 'tipo': atividade.tipo.nome}), 200

