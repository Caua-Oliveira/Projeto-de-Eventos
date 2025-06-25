from utils.db_models import db, Usuario, TipoUsuario, Evento, Atividade, InscricaoEvento
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ========== USUÁRIO ==========

def create_user(nome, email, senha):
    if Usuario.query.filter_by(email=email).first():
        return None, 'E-mail já cadastrado.'
    tipo = TipoUsuario.query.filter_by(nome='participante').first()
    if not tipo:
        return None, 'Tipo de usuário inválido.'
    hashed_password = generate_password_hash(senha)
    user = Usuario(nome=nome, email=email, senha=hashed_password, id_tipo_usuario=tipo.id_tipo_usuario)
    db.session.add(user)
    db.session.commit()
    return user, None

def authenticate_user(email, senha):
    user = Usuario.query.filter_by(email=email).first()
    if user and check_password_hash(user.senha, senha):
        return user
    return None

def get_all_usuarios():
    return Usuario.query.all()

def get_all_tipos_usuario():
    return TipoUsuario.query.all()

def update_user_tipo(user_id, novo_tipo_nome):
    user = Usuario.query.get(user_id)
    tipo = TipoUsuario.query.filter_by(nome=novo_tipo_nome).first()
    if not user or not tipo:
        raise Exception("Usuário ou tipo não encontrado.")
    user.id_tipo_usuario = tipo.id_tipo_usuario
    db.session.commit()

def delete_usuario(user_id):
    user = Usuario.query.get(user_id)
    if not user:
        raise Exception("Usuário não encontrado.")
    db.session.delete(user)
    db.session.commit()

# ========== EVENTOS ==========

def create_event(data):
    ev = Evento(
        titulo=data['titulo'],
        descricao=data.get('descricao'),
        local=data.get('local'),
        data_inicio=datetime.strptime(data['data_inicio'], '%Y-%m-%d').date(),
        data_fim=datetime.strptime(data['data_fim'], '%Y-%m-%d').date(),
        vagas=int(data['vagas']),
        imagem_url=data.get('imagem_url'),
        id_organizador=int(data['id_organizador']),
        online=data.get('online', False)
    )
    db.session.add(ev)
    db.session.flush()  # get ev.id_evento before commit
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
    return ev

def update_event(event_id, data):
    ev = Evento.query.get(event_id)
    if not ev:
        raise Exception('Evento não encontrado.')
    ev.titulo = data['titulo']
    ev.descricao = data.get('descricao')
    ev.local = data.get('local')
    ev.data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
    ev.data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
    ev.vagas = int(data['vagas'])
    ev.online = data.get('online', False)
    ev.finished = data.get('finished', False)
    if 'imagem_url' in data:
        ev.imagem_url = data['imagem_url']
    # Remove old activities and add new ones
    Atividade.query.filter_by(id_evento=ev.id_evento).delete()
    for atv in data.get('atividades', []):
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
    return ev

def delete_event(event_id):
    ev = Evento.query.get(event_id)
    if not ev:
        raise Exception('Evento não encontrado.')
    # Remove related activities
    Atividade.query.filter_by(id_evento=ev.id_evento).delete()
    db.session.delete(ev)
    db.session.commit()

def get_eventos(limit=10):
    return Evento.query.order_by(Evento.data_inicio).limit(limit).all()

def get_all_events():
    return Evento.query.order_by(Evento.data_inicio).all()

def get_evento_by_id(event_id):
    return Evento.query.get_or_404(event_id)

def get_atividades_by_event(event_id):
    return Atividade.query.filter_by(id_evento=event_id).order_by(Atividade.data_hora).all()

def count_eventos():
    return Evento.query.count()

# ========== INSCRIÇÃO ==========

def register_user_in_event(user_id, event_id):
    if InscricaoEvento.query.filter_by(id_usuario=user_id, id_evento=event_id).first():
        return False, "Usuário já inscrito neste evento."
    inscricao = InscricaoEvento(id_usuario=user_id, id_evento=event_id)
    evento = Evento.query.get(event_id)
    evento.vagas -= 1
    db.session.add(inscricao)
    db.session.commit()
    return True, None

def get_inscricao(user_id, event_id):
    return InscricaoEvento.query.filter_by(id_usuario=user_id, id_evento=event_id).first()

def get_inscricoes_by_user(user_id):
    return InscricaoEvento.query.filter_by(id_usuario=user_id).all()
def cancel_inscricao(user_id, event_id):
    inscricao = InscricaoEvento.query.filter_by(id_usuario=user_id, id_evento=event_id).first()
    if not inscricao:
        return False, "Inscrição não encontrada."
    evento = Evento.query.get(event_id)
    evento.vagas += 1
    db.session.delete(inscricao)
    db.session.commit()
    return True, None