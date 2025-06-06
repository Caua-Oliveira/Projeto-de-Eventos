from flask import redirect, url_for, session, flash
from functools import wraps
from app_utils.db_models import Usuario

def usuario_logado():
    uid = session.get('user_id')
    if not uid:
        return None
    return Usuario.query.get(uid)

def necessita_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not usuario_logado():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def necessita_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = usuario_logado()
        if not user or user.tipo.nome != 'admin':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function