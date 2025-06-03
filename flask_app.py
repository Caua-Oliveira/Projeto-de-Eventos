from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app_utils.utils import evento_to_dict
from app_utils.db_models import *

# Setup do flask e SQLAlchemy
app = Flask(__name__)
app.secret_key = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/plataforma_eventos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#
# Helpers (funções auxiliares)
#
def usuario_logado():
    # Se o usuario estiver logado, retorna o objeto Usuario correspondente
    uid = session.get('user_id')
    if not uid:
        return None
    return Usuario.query.get(uid)


def necessita_login(f):
    # Decorator para garantir que o usuário está logado antes de acessar uma rota
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not usuario_logado():
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def necessita_admin(f):
    # Decorator para garantir que o usuário é um administrador antes de acessar uma rota
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = usuario_logado()
        if not user or user.tipo.nome != 'admin':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)

    return decorated_function


#
# Rotas do flask (telas)
#
@app.route('/')
def inicio():
    if usuario_logado() and usuario_logado().tipo.nome == 'admin':
        return redirect(url_for('admin'))
    return render_template('inicio.html', user=usuario_logado())


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])  # Criptografa a senha
        tipo = TipoUsuario.query.filter_by(
            nome='participante').first()  # Automaticamente registra o usuario como participante
        if not tipo:
            flash('Tipo de usuário inválido.', 'danger')
            return redirect(url_for('cadastro'))
        user = Usuario(nome=nome, email=email, senha=senha, id_tipo_usuario=tipo.id_tipo_usuario)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha, senha):
            session['user_id'] = user.id_usuario
            flash('Bem-vindo, {}!'.format(user.nome), 'success')
            return redirect(url_for('inicio'))
        flash('Credenciais inválidas.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('inicio'))


@app.route('/eventos')
def eventos():
    eventos = Evento.query.order_by(Evento.data_inicio).all()
    return render_template('eventos.html', eventos=eventos, user=usuario_logado())


@app.route('/eventos/<int:event_id>')
def detalhes_evento(event_id):
    evento = Evento.query.get_or_404(event_id)
    atividades = Atividade.query.filter_by(id_evento=event_id).order_by(Atividade.data_hora).all()
    inscrito = False
    user = usuario_logado()
    if user:
        inscrito = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario, id_evento=event_id).first() is not None
    return render_template('detalhes_evento.html', evento=evento, atividades=atividades, inscrito=inscrito, user=user)

@app.route('/admin', methods=['GET', 'POST'])
@necessita_admin
def admin():
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()
    if request.method == 'POST':
        # Monta o payload para a API
        payload = {
            "titulo": request.form['titulo'],
            "descricao": request.form.get('descricao'),
            "local": request.form.get('local'),
            "data_inicio": request.form['data_inicio'],
            "data_fim": request.form['data_fim'],
            "vagas": int(request.form['vagas']),
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

        import requests
        resp = requests.post('http://127.0.0.1:5000/api/eventos', json=payload)
        if resp.status_code == 201:
            flash('Evento criado com sucesso!', 'success')
        else:
            flash(f'Erro ao criar evento: {resp.json().get("error", "Erro desconhecido")}', 'danger')
        return redirect(url_for('admin'))

    return render_template('admin.html', user=usuario_logado(), tipos=tipos)


@app.route('/perfil')
@necessita_login
def perfil():
    user = usuario_logado()
    minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
    return render_template('perfil.html', user=user, inscricoes=minhas_inscricoes)



# NOVO ENDPOINT API PARA CRIAÇÃO DE EVENTOS
@app.route('/api/eventos', methods=['POST'])
def api_criar_evento():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON ausentes'}), 400

    try:
        # Cria evento
        ev = Evento(
            titulo=data['titulo'],
            descricao=data.get('descricao'),
            local=data.get('local'),
            data_inicio=datetime.strptime(data['data_inicio'], '%Y-%m-%d').date(),
            data_fim=datetime.strptime(data['data_fim'], '%Y-%m-%d').date(),
            vagas=int(data['vagas']),
            id_organizador=int(data['id_organizador'])
        )
        db.session.add(ev)
        db.session.flush()  # Para pegar o id_evento

        # Cria atividades vinculadas
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

@app.route('/api/events/<int:evento_id>', methods=['GET'])
def api_detalhes_evento(evento_id):
    evento = Evento.query.get(evento_id)
    if not evento:
        return jsonify({'error': 'Evento nao encontrado'}), 404
    return jsonify(evento_to_dict(evento)), 200



if __name__ == '__main__':
    app.run(debug=True)