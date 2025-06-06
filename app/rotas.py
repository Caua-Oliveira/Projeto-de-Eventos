from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from app_utils.db_models import *
from app_utils.utils import upload_image_to_imgbb
from app_utils.rotas_helpers import usuario_logado, necessita_login, necessita_admin

rotas = Blueprint('rotas', __name__)

@rotas.route('/')
def inicio():
    if usuario_logado() and usuario_logado().tipo.nome == 'admin':
        return redirect(url_for('routes.admin'))
    return render_template('inicio.html', user=usuario_logado(),
                           eventos=Evento.query.order_by(Evento.data_inicio).limit(10).all())

@rotas.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        resp = requests.post('http://127.0.0.1:5000/api/cadastro', json={
            'nome': nome,
            'email': email,
            'senha': senha
        })
        if resp.status_code == 201:
            flash('Cadastro realizado! Faça login.', 'success')
            return redirect(url_for('routes.login'))
        else:
            flash(resp.json().get('error', 'Erro ao cadastrar usuário.'), 'danger')
            return redirect(url_for('routes.cadastro'))
    return render_template('cadastro.html')

@rotas.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('routes.inicio'))
        else:
            flash(resp.json().get('error', 'Credenciais inválidas.'), 'danger')
    return render_template('login.html')

@rotas.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('routes.inicio'))

@rotas.route('/eventos')
def eventos():
    eventos = Evento.query.order_by(Evento.data_inicio).all()
    return render_template('eventos.html', eventos=eventos, user=usuario_logado())

@rotas.route('/eventos/<int:event_id>')
def detalhes_evento(event_id):
    evento = Evento.query.get_or_404(event_id)
    atividades = Atividade.query.filter_by(id_evento=event_id).order_by(Atividade.data_hora).all()
    inscrito = False
    user = usuario_logado()
    if user:
        inscrito = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario, id_evento=event_id).first() is not None
    return render_template('detalhes_evento.html', evento=evento, atividades=atividades, inscrito=inscrito, user=user)

@rotas.route('/admin', methods=['GET', 'POST'])
@necessita_admin
def admin():
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()
    if request.method == 'POST':
        imagem = request.files.get('imagem_evento')
        imagem_url = None
        if imagem:
            imagem_url = upload_image_to_imgbb(imagem)
            if not imagem_url:
                flash('Erro ao fazer upload da imagem.', 'danger')
        payload = {
            "titulo": request.form['titulo'],
            "descricao": request.form.get('descricao'),
            "local": request.form.get('local'),
            "data_inicio": request.form['data_inicio'],
            "data_fim": request.form['data_fim'],
            "vagas": int(request.form['vagas']),
            "imagem_url": imagem_url,
            "id_organizador": usuario_logado().id_usuario,
            "atividades": []
        }
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
                "data_hora": datash[i],  # espera-se formato 'YYYY-MM-DDTHH:MM'
                "duracao_minutos": int(duracoes[i]),
                "id_tipo_atividade": int(tipos_ids[i])
            })

        resp = requests.post('http://127.0.0.1:5000/api/eventos', json=payload)
        if resp.status_code == 201:
            flash('Evento criado com sucesso!', 'success')
        else:
            flash(f'Erro ao criar evento: {resp.json().get("error", "Erro desconhecido")}', 'danger')
        return redirect(url_for('routes.admin'))

    return render_template('admin.html', user=usuario_logado(), tipos=tipos)

@rotas.route('/perfil')
@necessita_login
def perfil():
    user = usuario_logado()
    minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
    return render_template('perfil.html', user=user, inscricoes=minhas_inscricoes)