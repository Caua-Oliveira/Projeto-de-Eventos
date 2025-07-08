from flask import Blueprint, render_template, send_from_directory, current_app

docs = Blueprint('docs', __name__)

@docs.route('/openapi.json')
def openapi_json():
    return send_from_directory(current_app.static_folder, 'openapi.json')

@docs.route('/docs')
def docs_swagger():
    return render_template('swaggerui.html')