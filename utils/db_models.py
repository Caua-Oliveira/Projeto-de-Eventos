from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
    imagem_url = db.Column(db.String(500), nullable=True)
    online = db.Column(db.Boolean, nullable=False, default=False)  # Add this line

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