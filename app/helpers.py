from flask import redirect, url_for, session, flash, jsonify, request
from functools import wraps
from utils.db_models import Usuario

def logged_user():
    uid = session.get('user_id')
    if not uid:
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Here you would look up the user by API key
            # This is a placeholder for actual API key authentication
            user = Usuario.query.filter_by(email=api_key).first()
            return user
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
            return redirect(url_for('rotas.home'))
        return f(*args, **kwargs)
    return is_admin

def api_requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not logged_user():
            return jsonify({'error': 'Acesso não autorizado. Faça o login.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def api_requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = logged_user()
        if not user or user.tipo.nome != 'admin':
            return jsonify({'error': 'Acesso negado. Requer privilégios de administrador.'}), 403
        return f(*args, **kwargs)
    return decorated_function
