from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from utils.db_models import *
from utils.utils import upload_image_to_imgbb
from app.helpers import logged_user, requires_login, requires_admin

routes = Blueprint('rotas', __name__)

@routes.route('/')
def home():
    return render_template('home.html', user=logged_user(),
                           events=Evento.query.order_by(Evento.data_inicio).limit(10).all())

@routes.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        resp = requests.post('http://127.0.0.1:5000/api/sign_up', json={
            'nome': nome,
            'email': email,
            'senha': senha
        })
        if resp.status_code == 201:
            flash('sign_up realizado! Faça login.', 'success')
            return redirect(url_for('rotas.login'))
        else:
            flash(resp.json().get('error', 'Erro ao cadastrar usuário.'), 'danger')
            return redirect(url_for('rotas.sign_up'))
    return render_template('sign_up.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        resp = requests.post('http://127.0.0.1:5000/api/login', json={
            'email': email,
            'senha': senha
        })
        if resp.status_code == 200:
            user = resp.json()['user']
            session['user_id'] = user['id_usuario']
            flash('Bem-vindo, {}!'.format(user['nome']), 'success')
            return redirect(url_for('rotas.home'))
        else:
            flash(resp.json().get('error', 'Credenciais inválidas.'), 'danger')
    return render_template('login.html')

@routes.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('rotas.home'))

@routes.route('/events')
def events():
    events = Evento.query.order_by(Evento.data_inicio).all()
    return render_template('events.html', events=events, user=logged_user())

@routes.route('/events/<int:event_id>')
def event_details(event_id):
    evento = Evento.query.get_or_404(event_id)
    atividades = Atividade.query.filter_by(id_evento=event_id).order_by(Atividade.data_hora).all()
    inscrito = False
    user = logged_user()
    if user:
        inscrito = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario, id_evento=event_id).first() is not None
    return render_template('event_details.html', evento=evento, atividades=atividades, inscrito=inscrito, user=user)

@routes.route('/profile')
@requires_login
def profile():
    user = logged_user()
    minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
    return render_template('profile.html', user=user, inscricoes=minhas_inscricoes)



# === ROTAS ADMINISTRATIVAS ===
@routes.route('/admin')
@requires_admin
def admin():
    """Dashboard administrativo"""
    # Estatísticas
    total_eventos = Evento.query.count()
    total_usuarios = Usuario.query.count()
    total_admins = Usuario.query.join(TipoUsuario).filter(TipoUsuario.nome == 'admin').count()
    total_organizadores = Usuario.query.join(TipoUsuario).filter(TipoUsuario.nome == 'organizador').count()

    # Eventos recentes
    eventos_recentes = Evento.query.order_by(Evento.data_inicio.desc()).limit(5).all()

    stats = {
        'total_eventos': total_eventos,
        'total_usuarios': total_usuarios,
        'total_admins': total_admins,
        'total_organizadores': total_organizadores
    }

    return render_template('admin/dashboard.html',
                           user=logged_user(),
                           stats=stats,
                           eventos_recentes=eventos_recentes)


@routes.route('/admin/eventos')
@requires_admin
def admin_eventos():
    """Gerenciar eventos"""
    eventos = Evento.query.order_by(Evento.data_inicio.desc()).all()
    return render_template('admin/eventos.html',
                           user=logged_user(),
                           eventos=eventos)


@routes.route('/admin/usuarios')
@requires_admin
def admin_usuarios():
    """Gerenciar usuários"""
    usuarios = Usuario.query.all()
    tipos_usuario = TipoUsuario.query.all()
    return render_template('admin/usuarios.html',
                           user=logged_user(),
                           usuarios=usuarios,
                           tipos_usuario=tipos_usuario)


@routes.route('/admin/criar-evento', methods=['GET', 'POST'])
@requires_admin
def admin_criar_evento():
    """Criar novo evento"""
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()

    if request.method == 'POST':
        # Upload da imagem
        imagem = request.files.get('imagem_evento')
        imagem_url = None
        if imagem:
            imagem_url = upload_image_to_imgbb(imagem)
            if not imagem_url:
                flash('Erro ao fazer upload da imagem.', 'danger')

        # Dados do evento
        payload = {
            "titulo": request.form['titulo'],
            "descricao": request.form.get('descricao'),
            "local": request.form.get('local'),
            "data_inicio": request.form['data_inicio'],
            "data_fim": request.form['data_fim'],
            "vagas": int(request.form['vagas']),
            "imagem_url": imagem_url,
            "id_organizador": logged_user().id_usuario,
            "atividades": []
        }

        # Coletar atividades
        titulos = request.form.getlist('titulo_atividade')
        descricoes = request.form.getlist('descricao_atividade')
        datash = request.form.getlist('data_hora_atividade')
        duracoes = request.form.getlist('duracao_atividade')
        tipos_ids = request.form.getlist('tipo_atividade')

        for i, t in enumerate(titulos):
            if not t.strip():
                continue
            payload["atividades"].append({
                "titulo": t,
                "descricao": descricoes[i] or None,
                "data_hora": datash[i],
                "duracao_minutos": int(duracoes[i]),
                "id_tipo_atividade": int(tipos_ids[i])
            })

        # Criar evento via API
        resp = requests.post('http://127.0.0.1:5000/api/events', json=payload)
        if resp.status_code == 201:
            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('rotas.admin_eventos'))
        else:
            flash(f'Erro ao criar evento: {resp.json().get("error", "Erro desconhecido")}', 'danger')

    return render_template('admin/criar_evento.html',
                           user=logged_user(),
                           tipos=tipos)


@routes.route('/admin/editar-evento/<int:evento_id>', methods=['GET', 'POST'])
@requires_admin
def admin_editar_evento(evento_id):
    """Editar evento existente"""
    evento = Evento.query.get_or_404(evento_id)
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()
    atividades = Atividade.query.filter_by(id_evento=evento_id).all()

    if request.method == 'POST':
        # Dados atualizados do evento
        payload = {
            "titulo": request.form['titulo'],
            "descricao": request.form.get('descricao'),
            "local": request.form.get('local'),
            "data_inicio": request.form['data_inicio'],
            "data_fim": request.form['data_fim'],
            "vagas": int(request.form['vagas']),
            "online": 'online' in request.form,
            "atividades": []
        }

        # Upload de nova imagem (se fornecida)
        imagem = request.files.get('imagem_evento')
        if imagem:
            imagem_url = upload_image_to_imgbb(imagem)
            if imagem_url:
                payload["imagem_url"] = imagem_url

        # Coletar atividades
        titulos = request.form.getlist('titulo_atividade')
        descricoes = request.form.getlist('descricao_atividade')
        datash = request.form.getlist('data_hora_atividade')
        duracoes = request.form.getlist('duracao_atividade')
        tipos_ids = request.form.getlist('tipo_atividade')

        for i, t in enumerate(titulos):
            if not t.strip():
                continue
            payload["atividades"].append({
                "titulo": t,
                "descricao": descricoes[i] or None,
                "data_hora": datash[i],
                "duracao_minutos": int(duracoes[i]),
                "id_tipo_atividade": int(tipos_ids[i])
            })

        # Atualizar evento via API
        resp = requests.put(f'http://127.0.0.1:5000/api/events/{evento_id}', json=payload)
        if resp.status_code == 200:
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('rotas.admin_eventos'))
        else:
            flash(f'Erro ao atualizar evento: {resp.json().get("error", "Erro desconhecido")}', 'danger')

    return render_template('admin/editar_evento.html',
                           user=logged_user(),
                           evento=evento,
                           atividades=atividades,
                           tipos=tipos)


@routes.route('/admin/deletar-evento/<int:evento_id>', methods=['POST'])
@requires_admin
def admin_deletar_evento(evento_id):
    """Deletar evento"""
    resp = requests.delete(f'http://127.0.0.1:5000/api/events/{evento_id}')
    if resp.status_code == 200:
        flash('Evento deletado com sucesso!', 'success')
    else:
        flash(f'Erro ao deletar evento: {resp.json().get("error", "Erro desconhecido")}', 'danger')

    return redirect(url_for('rotas.admin_eventos'))


@routes.route('/admin/alterar-tipo-usuario/<int:user_id>', methods=['POST'])
@requires_admin
def admin_alterar_tipo_usuario(user_id):
    """Alterar tipo de usuário"""
    novo_tipo = request.form['tipo']

    resp = requests.put(f'http://127.0.0.1:5000/api/users/{user_id}/tipo',
                        json={'tipo': novo_tipo})
    if resp.status_code == 200:
        flash('Tipo de usuário atualizado com sucesso!', 'success')
    else:
        flash(f'Erro ao atualizar tipo de usuário: {resp.json().get("error", "Erro desconhecido")}', 'danger')

    return redirect(url_for('rotas.admin_usuarios'))


@routes.route('/admin/deletar-usuario/<int:user_id>', methods=['POST'])
@requires_admin
def admin_deletar_usuario(user_id):
    """Deletar usuário"""
    resp = requests.delete(f'http://127.0.0.1:5000/api/users/{user_id}')
    if resp.status_code == 200:
        flash('Usuário deletado com sucesso!', 'success')
    else:
        flash(f'Erro ao deletar usuário: {resp.json().get("error", "Erro desconhecido")}', 'danger')

    return redirect(url_for('rotas.admin_usuarios'))