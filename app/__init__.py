from flask import Flask
from app.routes import routes
from app.api import api
from app_utils.db_models import db
import os
import json

secrets_path = os.path.abspath(os.path.join(__file__, '..', '..', 'secrets.json'))
with open(secrets_path) as f:
    secrets = json.load(f)
db_url = secrets.get('railway_db_url')

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, 'templates'),
        static_folder=os.path.join(root_dir, 'static')
    )
    app.secret_key = 'secretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(routes)
    app.register_blueprint(api, url_prefix='/api')

    return app
