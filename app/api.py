from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app_utils.db_models import db, Usuario, TipoUsuario, Evento, Atividade
from app_utils.utils import evento_to_dict

api = Blueprint('api', __name__)

@api.route('/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    if not (nome and email and senha):
        return jsonify({'error': 'Nome, email e senha são obrigatórios.'}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({'error': 'E-mail já cadastrado.'}), 400
    tipo = TipoUsuario.query.filter_by(nome='participante').first()
    if not tipo:
        return jsonify({'error': 'Tipo de usuário inválido.'}), 400
    hashed_password = generate_password_hash(senha)
    user = Usuario(nome=nome, email=email, senha=hashed_password, id_tipo_usuario=tipo.id_tipo_usuario)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'id_usuario': user.id_usuario}), 201

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400
    email = data.get('email')
    senha = data.get('senha')
    if not (email and senha):
        return jsonify({'error': 'Email e senha são obrigatórios.'}), 400
    user = Usuario.query.filter_by(email=email).first()
    if user and check_password_hash(user.senha, senha):
        user_json = {
            'id_usuario': user.id_usuario,
            'nome': user.nome,
            'email': user.email,
            'tipo': user.tipo.nome
        }
        return jsonify({'success': True, 'user': user_json}), 200
    return jsonify({'error': 'Credenciais inválidas.'}), 401

@api.route('/eventos', methods=['POST'])
def criar_evento():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400

    try:
        ev = Evento(
            titulo=data['titulo'],
            descricao=data.get('descricao'),
            local=data.get('local'),
            data_inicio=datetime.strptime(data['data_inicio'], '%Y-%m-%d').date(),
            data_fim=datetime.strptime(data['data_fim'], '%Y-%m-%d').date(),
            vagas=int(data['vagas']),
            imagem_url=data.get('imagem_url'),
            id_organizador=int(data['id_organizador'])
        )
        db.session.add(ev)
        db.session.flush()

        atividades = data.get('atividades', [])
        for atv in atividades:
            atividade = Atividade(
                id_evento=ev.id_evento,
                titulo=atv['titulo'],
                descricao=atv.get('descricao'),
                data_hora=datetime.strptime(atv['data_hora'], '%Y-%m-%dT%H:%M'),
                duracao_minutos=int(atv['duracao_minutos']),
                id_tipo_atividade=int(atv['id_tipo_atividade'])
            )
            db.session.add(atividade)

        db.session.commit()

        return jsonify({'success': True, 'id_evento': ev.id_evento}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/events/<int:evento_id>', methods=['GET'])
def detalhes_evento(evento_id):
    evento = Evento.query.get(evento_id)
    if not evento:
        return jsonify({'error': 'Evento nao encontrado'}), 404
    return jsonify(evento_to_dict(evento)), 200