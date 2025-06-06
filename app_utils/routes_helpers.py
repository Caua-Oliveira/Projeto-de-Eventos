from flask import redirect, url_for, session, flash
from functools import wraps
from app_utils.db_models import Usuario

def logged_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return Usuario.query.get(uid)

def requires_login(f):
    @wraps(f)
    def is_logged(*args, **kwargs):
        if not logged_user():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return is_logged

def requires_admin(f):
    @wraps(f)
    def is_admin(*args, **kwargs):
        user = logged_user()
        if not user or user.tipo.nome != 'admin':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return is_admin