from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Setup do flask e SQLAlchemy
app = Flask(__name__)
app.secret_key = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/plataforma_eventos_2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


#
# Modelos da database (para utilizar o MySql)
#
class TipoUsuario(db.Model):
    __tablename__ = 'tipos_usuario'
    id_tipo_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    id_tipo_usuario = db.Column(db.Integer, db.ForeignKey('tipos_usuario.id_tipo_usuario'), nullable=False)
    tipo = db.relationship('TipoUsuario')


class Evento(db.Model):
    __tablename__ = 'eventos'
    id_evento = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    local = db.Column(db.String(150))
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    vagas = db.Column(db.Integer, nullable=False, default=0)
    id_organizador = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    organizador = db.relationship('Usuario')


class TipoAtividade(db.Model):
    __tablename__ = 'tipos_atividade'
    id_tipo_atividade = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)


class Atividade(db.Model):
    __tablename__ = 'atividades'
    id_atividade = db.Column(db.Integer, primary_key=True)
    id_evento = db.Column(db.Integer, db.ForeignKey('eventos.id_evento'), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer)
    id_tipo_atividade = db.Column(db.Integer, db.ForeignKey('tipos_atividade.id_tipo_atividade'), nullable=False)
    evento = db.relationship('Evento')
    tipo = db.relationship('TipoAtividade')


class InscricaoEvento(db.Model):
    __tablename__ = 'inscricoes_evento'
    id_inscricao_evento = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_evento = db.Column(db.Integer, db.ForeignKey('eventos.id_evento'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario')
    evento = db.relationship('Evento')


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
    # Se o usuario for um admin, vai direto para a pagina de admins, se não, vai para a tela de inicio
    if usuario_logado() and usuario_logado().tipo.nome == 'admin':
        return redirect(url_for('admin'))
    return render_template('inicio.html', user=usuario_logado())


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # Quando o botão de registro for clicado, o "method" vai ser POST
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])  # Criptografa a senha
        tipo = TipoUsuario.query.filter_by(
            nome='participante').first()  # Automaticamente registra o usuario como participante
        if not tipo:
            flash('Tipo de usuário inválido.', 'danger')
            return redirect(url_for('registro'))
        user = Usuario(nome=nome, email=email, senha=senha, id_tipo_usuario=tipo.id_tipo_usuario)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado! Faça login.', 'success')
        return redirect(url_for('login'))

    # Se o método não for POST, rederiza a página.
    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Quando o botão de login for clicado, o "method" vai ser POST
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha, senha):
            session['user_id'] = user.id_usuario
            flash('Bem-vindo, {}!'.format(user.nome), 'success')
            return redirect(url_for('inicio'))
        flash('Credenciais inválidas.', 'danger')

    # Se o método não for POST, rederiza a página.
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('inicio'))


@app.route('/eventos')
def eventos():
    # Lista todos os eventos ordenados pela data de início e entrega como parametro para a página de eventos
    # (em eventos.html se usa um loop para exibir os eventos)
    eventos = Evento.query.order_by(Evento.data_inicio).all()
    return render_template('eventos.html', eventos=eventos, user=usuario_logado())


@app.route('/eventos/<int:event_id>')
def detalhes_evento(event_id):
    # Busca o evento pelo ID e suas atividades, verifica se o usuário está inscrito
    # e entrega como parametro para a página de detalhes do evento
    evento = Evento.query.get_or_404(event_id)
    atividades = Atividade.query.filter_by(id_evento=event_id).order_by(Atividade.data_hora).all()
    inscrito = False
    user = usuario_logado()
    if user:
        inscrito = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario, id_evento=event_id).first() is not None
    return render_template('detalhes_evento.html', evento=evento, atividades=atividades, inscrito=inscrito, user=user)


@app.route('/admin', methods=['GET', 'POST'])
@necessita_admin  # Decorator para garantir que apenas administradores acessem essa rota
def admin():
    tipos = TipoAtividade.query.order_by(TipoAtividade.nome).all()
    if request.method == 'POST':
        # 1) cria evento
        ev = Evento(
            titulo=request.form['titulo'],
            descricao=request.form.get('descricao'),
            local=request.form.get('local'),
            data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
            data_fim=datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date(),
            vagas=int(request.form['vagas']),
            id_organizador=usuario_logado().id_usuario
        )
        db.session.add(ev)
        db.session.flush()  # para ter ev.id_evento antes de commit

        # 2) cria atividades vinculadas
        titulos = request.form.getlist('titulo_atividade')
        descricoes = request.form.getlist('descricao_atividade')
        datash = request.form.getlist('data_hora_atividade')
        duracoes = request.form.getlist('duracao_atividade')
        tipos_ids = request.form.getlist('tipo_atividade')

        for i, t in enumerate(titulos):
            if not t.strip():
                continue
            atividade = Atividade(
                id_evento=ev.id_evento,
                titulo=t,
                descricao=descricoes[i] or None,
                data_hora=datetime.strptime(datash[i], '%Y-%m-%dT%H:%M'),
                duracao_minutos=int(duracoes[i]),
                id_tipo_atividade=int(tipos_ids[i])
            )
            db.session.add(atividade)

        db.session.commit()
        flash('Evento e atividades criados com sucesso!', 'success')
        return redirect(url_for('admin'))

    return render_template('admin.html', user=usuario_logado(), tipos=tipos)


# TEM QUE COLOCAR A PAGINA DE REGISTRO AOS EVENTOS AINDA
# Atualmente quando clica em "Registrar-se" em um evento, ele registra o usuario automaticamenta (sem uma página para isso)
# e depois retorna para a pagina de detalhes do evento
# Para isso precisa adicionar o method 'GET' e "render_template()" o html da pagina
@app.route('/eventos/<int:event_id>/registro', methods=['POST'])
@necessita_login  # Decorator para garantir que o usuário está logado antes de registrar-se em um evento
def register_event(event_id):
    user = usuario_logado()
    evento = Evento.query.get_or_404(event_id)
    inscritos = InscricaoEvento.query.filter_by(id_evento=event_id).count()
    if inscritos >= evento.vagas:
        flash('Não há vagas disponíveis.', 'warning')
    else:
        insc = InscricaoEvento(id_usuario=user.id_usuario, id_evento=event_id)
        db.session.add(insc)
        db.session.commit()
        flash('Inscrição realizada!', 'success')
    return redirect(url_for('detalhes_evento', event_id=event_id))


@app.route('/perfil')
@necessita_login # Decorator para garantir que o usuário está logado antes de acessar o perfil
def perfil():
    user = usuario_logado()
    minhas_inscricoes = InscricaoEvento.query.filter_by(id_usuario=user.id_usuario).all()
    return render_template('perfil.html', user=user, inscricoes=minhas_inscricoes)


if __name__ == '__main__':
    app.run(debug=True)
