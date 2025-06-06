from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app_utils.utils import evento_to_dict, upload_image_to_imgbb
from app_utils.db_models import *

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