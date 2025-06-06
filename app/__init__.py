from flask import Flask
from app import rotas
from app.api import api
from app_utils.db_models import db

def create_app():
    app = Flask(__name__)
    app.secret_key = 'secretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/plataforma_eventos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(rotas)
    app.register_blueprint(api, url_prefix='/api')

    return app