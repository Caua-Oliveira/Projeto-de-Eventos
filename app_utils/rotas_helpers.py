from flask import redirect, url_for, session, flash
from functools import wraps
from app_utils.db_models import Usuario

def user_is_logged_in():
    uid = session.get('user_id')
    if not uid:
        return None
    return Usuario.query.get(uid)

def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user_is_logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = user_is_logged_in()
        if not user or user.tipo.nome != 'admin':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function