from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from utils.db_models import db, Usuario, TipoUsuario, Evento, Atividade, InscricaoEvento
from utils.utils import event_to_dict

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
def api_login():
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


@api.route('/events', methods=['POST'])
def api_create_event():
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
            id_organizador=int(data['id_organizador']),
            online=data.get('online', False)  # Add this line
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
def api_event_details(evento_id):
    evento = Evento.query.get(evento_id)
    if not evento:
        return jsonify({'error': 'Evento nao encontrado'}), 404
    return jsonify(event_to_dict(evento)), 200


# NOVAS ROTAS PARA O PAINEL ADMINISTRATIVO

@api.route('/events', methods=['GET'])
def api_list_events():
    """Lista todos os eventos"""
    try:
        quantidade = request.args.get('quantidade', type=int)
        query = Evento.query.order_by(Evento.data_inicio.desc())
        if quantidade is not None:
            eventos = query.limit(quantidade).all()
        else:
            eventos = query.all()
        eventos_list = []
        for evento in eventos:
            eventos_list.append({
                'id_evento': evento.id_evento,
                'titulo': evento.titulo,
                'descricao': evento.descricao,
                'local': evento.local,
                'data_inicio': evento.data_inicio.strftime('%d/%m/%Y'),
                'data_fim': evento.data_fim.strftime('%d/%m/%Y'),
                'vagas': evento.vagas,
                'online': evento.online,
                'organizador': evento.organizador.nome if evento.organizador else 'N/A'
            })
        return jsonify({'eventos': eventos_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/events/<int:evento_id>', methods=['PUT'])
def api_update_event(evento_id):
    """Atualiza um evento existente"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400

    try:
        evento = Evento.query.get(evento_id)
        if not evento:
            return jsonify({'error': 'Evento não encontrado'}), 404

        # Atualizar dados do evento
        evento.titulo = data.get('titulo', evento.titulo)
        evento.descricao = data.get('descricao', evento.descricao)
        evento.local = data.get('local', evento.local)
        evento.online = data.get('online', evento.online)  # Add this line

        if 'data_inicio' in data:
            evento.data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
        if 'data_fim' in data:
            evento.data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
        if 'vagas' in data:
            evento.vagas = int(data['vagas'])
        if 'imagem_url' in data:
            evento.imagem_url = data['imagem_url']

        # Handle activities update logic here...

        db.session.commit()
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/events/<int:evento_id>', methods=['DELETE'])
def api_delete_event(evento_id):
    """Deleta um evento"""
    try:
        evento = Evento.query.get(evento_id)
        if not evento:
            return jsonify({'error': 'Evento não encontrado'}), 404

        # Deletar atividades relacionadas primeiro
        Atividade.query.filter_by(id_evento=evento_id).delete()

        # Deletar o evento
        db.session.delete(evento)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Evento deletado com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/users', methods=['GET'])
def api_list_users():
    """Lista todos os usuários"""
    try:
        usuarios = Usuario.query.all()
        usuarios_list = []
        for usuario in usuarios:
            usuarios_list.append({
                'id_usuario': usuario.id_usuario,
                'nome': usuario.nome,
                'email': usuario.email,
                'tipo': usuario.tipo.nome
            })
        return jsonify({'usuarios': usuarios_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """Deleta um usuário"""
    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        db.session.delete(usuario)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Usuário deletado com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/users/<int:user_id>/tipo', methods=['PUT'])
def api_update_user_type(user_id):
    """Atualiza o tipo de um usuário"""
    data = request.get_json()
    if not data or 'tipo' not in data:
        return jsonify({'error': 'Tipo de usuário é obrigatório'}), 400

    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        tipo = TipoUsuario.query.filter_by(nome=data['tipo']).first()
        if not tipo:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400

        usuario.id_tipo_usuario = tipo.id_tipo_usuario
        db.session.commit()

        return jsonify({'success': True, 'message': 'Tipo de usuário atualizado com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


#Api for listing user information
@api.route('/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """Obtém informações de um usuário específico"""
    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        user_info = {
            'id_usuario': usuario.id_usuario,
            'nome': usuario.nome,
            'email': usuario.email,
            'tipo': usuario.tipo.nome
        }
        return jsonify({'usuario': user_info}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Api for listing all events a user is registered for
@api.route('/users/<int:user_id>/events', methods=['GET'])
def api_get_user_events(user_id):
    """Obtém todos os eventos em que um usuário está inscrito"""
    try:
        usuario = Usuario.query.get(user_id)
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        inscricoes = InscricaoEvento.query.filter_by(id_usuario=usuario.id_usuario).all()
        eventos_list = []

        for inscricao in inscricoes:
            evento = inscricao.evento
            eventos_list.append(event_to_dict(evento))
        return jsonify({'eventos': eventos_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/events/<int:evento_id>/register', methods=['POST'])
def api_register_to_event(evento_id):
    """Inscreve um usuário em um evento, se tiver vagas disponíveis"""
    data = request.get_json()
    if not data or 'id_usuario' not in data:
        return jsonify({'error': 'Dados JSON ausentes ou id_usuario não fornecido'}), 400

    try:
        usuario = Usuario.query.get(data['id_usuario'])
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        evento = Evento.query.get(evento_id)
        if not evento:
            return jsonify({'error': 'Evento não encontrado'}), 404

        if evento.vagas <= 0:
            return jsonify({'error': 'Não há vagas disponíveis para este evento.'}), 400

        inscricao_existente = InscricaoEvento.query.filter_by(id_usuario=usuario.id_usuario, id_evento=evento_id).first()
        if inscricao_existente:
            return jsonify({'error': 'Usuário já inscrito neste evento.'}), 400

        inscricao = InscricaoEvento(id_usuario=usuario.id_usuario, id_evento=evento_id)
        db.session.add(inscricao)
        db.session.commit()

        # Decrementar vagas disponíveis
        evento.vagas -= 1
        db.session.commit()

        return jsonify({'success': True, 'message': 'Usuário inscrito com sucesso.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


