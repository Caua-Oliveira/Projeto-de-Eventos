from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.utils import upload_image_to_imgbb
from app.helpers import logged_user, requires_login, requires_admin
from app.db_operations import *
from utils.db_models import TipoAtividade

routes = Blueprint('rotas', __name__)

@routes.route('/')
def home():
    return render_template('home.html', user=logged_user(),
                           events=get_eventos())

@routes.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        from app.db_operations import create_user
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        user, error = create_user(nome, email, senha)
        if not error:
            flash('sign_up realizado! Faça login.', 'success')
            return redirect(url_for('rotas.login'))
        else:
            flash(error or 'Erro ao cadastrar usuário.', 'danger')
            return redirect(url_for('rotas.sign_up'))
    return render_template('sign_up.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from app.db_operations import authenticate_user
        email = request.form['email']
        senha = request.form['senha']
        user = authenticate_user(email, senha)
        if user:
            session['user_id'] = user.id_usuario
            flash('Bem-vindo, {}!'.format(user.nome), 'success')
            return redirect(url_for('rotas.home'))
        else:
            flash('Credenciais inválidas.', 'danger')
    return render_template('login.html')

@routes.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('rotas.home'))

@routes.route('/events')
def events():
    has_param = 'online' in request.args or 'irl' in request.args
    show_online = request.args.get('online') == '1' or not has_param
    show_irl = request.args.get('irl') == '1' or not has_param


    if show_online and show_irl:
        events = Evento.query.all()
    elif show_online:
        events = Evento.query.filter_by(online=True).all()
    elif show_irl:
        events = Evento.query.filter_by(online=False).all()
    else:
        events = []
    return render_template('events.html', events=events, user=logged_user(), show_online=show_online, show_irl=show_irl)

@routes.route('/events/<int:event_id>')
def event_details(event_id):
    evento = get_evento_by_id(event_id)
    atividades = get_atividades_by_event(event_id)
    inscrito = False
    user = logged_user()
    if user:
        inscrito = get_inscricao(user.id_usuario, event_id) is not None
    return render_template('event_details.html', evento=evento, atividades=atividades, inscrito=inscrito, user=user)

@routes.route('/profile')
@requires_login
def profile():
    user = logged_user()
    minhas_inscricoes = get_inscricoes_by_user(user.id_usuario)
    return render_template('profile.html', user=user, inscricoes=minhas_inscricoes)

@routes.route('/events/<int:event_id>/inscrever', methods=['POST'])
@requires_login
def register_in_event(event_id):
    user = logged_user()
    success, error = register_user_in_event(user.id_usuario, event_id)
    if success:
        flash('Inscrição realizada com sucesso!', 'success')
    else:
        flash(error or 'Erro ao se inscrever no evento.', 'danger')
    return redirect(url_for('rotas.event_details', event_id=event_id))

# === ROTAS ADMINISTRATIVAS ===
@routes.route('/admin')
@requires_admin
def admin():
    # Dashboard administrativo
    stats = {
        'total_eventos': count_eventos(),
        'total_usuarios': 0,
        'total_admins': 0,
        'total_organizadores': 0
    }
    eventos_recentes = [e for e in get_all_events()]
    usuarios = get_all_usuarios()
    stats['total_usuarios'] = len(usuarios)
    stats['total_admins'] = sum(1 for u in usuarios if u.tipo.nome == 'admin')
    stats['total_organizadores'] = sum(1 for u in usuarios if u.tipo.nome == 'organizador')
    eventos_recentes = sorted(eventos_recentes, key=lambda e: e.data_inicio, reverse=True)[:5]
    return render_template('admin/dashboard.html',
                           user=logged_user(),
                           stats=stats,
                           eventos_recentes=eventos_recentes)

@routes.route('/admin/eventos')
@requires_admin
def admin_events():
    eventos = get_all_events()
    return render_template('admin/events.html',
                           user=logged_user(),
                           eventos=eventos)

@routes.route('/admin/usuarios')
@requires_admin
def admin_users():
    usuarios = get_all_usuarios()
    tipos_usuario = get_all_tipos_usuario()
    return render_template('admin/users.html',
                           user=logged_user(),
                           usuarios=usuarios,
                           tipos_usuario=tipos_usuario)

@routes.route('/admin/criar-evento', methods=['GET', 'POST'])
@requires_admin
def admin_create_event():
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

        # Criar evento via DB operations
        try:
            create_event(payload)
            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('rotas.admin_eventos'))
        except Exception as e:
            flash(f'Erro ao criar evento: {e}', 'danger')

    return render_template('admin/create_event.html',
                           user=logged_user(),
                           tipos=tipos)

@routes.route('/admin/editar-evento/<int:event_id>', methods=['GET', 'POST'])
@requires_admin
def admin_edit_event(event_id):
    evento = get_evento_by_id(event_id)
    atividades = get_atividades_by_event(event_id)
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()

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

        # Atualizar evento via DB operations
        try:
            update_event(event_id, payload)
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('rotas.admin_eventos'))
        except Exception as e:
            flash(f'Erro ao atualizar evento: {e}', 'danger')

    return render_template('admin/edit_event.html',
                           user=logged_user(),
                           evento=evento,
                           atividades=atividades,
                           tipos=tipos)

@routes.route('/admin/deletar-evento/<int:event_id>', methods=['POST'])
@requires_admin
def admin_delete_event(event_id):
    try:
        delete_event(event_id)
        flash('Evento deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar evento: {e}', 'danger')

    return redirect(url_for('rotas.admin_events'))

@routes.route('/admin/alterar-tipo-usuario/<int:user_id>', methods=['POST'])
@requires_admin
def admin_alterar_tipo_usuario(user_id):
    novo_tipo = request.form['tipo']
    try:
        update_user_tipo(user_id, novo_tipo)
        flash('Tipo de usuário atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar tipo de usuário: {e}', 'danger')

    return redirect(url_for('rotas.admin_users'))

@routes.route('/admin/deletar-usuario/<int:user_id>', methods=['POST'])
@requires_admin
def admin_deletar_usuario(user_id):
    try:
        delete_usuario(user_id)
        flash('Usuário deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar usuário: {e}', 'danger')

    return redirect(url_for('rotas.admin_users')
)