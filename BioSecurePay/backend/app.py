from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from config import Config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from routes import bp as api_bp
import os

app = Flask(__name__, static_folder='build', static_url_path='/')
app.config.from_object(Config)

if app.config.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

mongo = PyMongo(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/v1/*": {"origins": ["https://biosecure-pay.onrender.com", "http://localhost:3000"]}})

app.register_blueprint(api_bp, url_prefix='/api/v1')

@app.route('/api')
def api_status():
    return jsonify({"status": "BioSecurePay API is running!"})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    if not os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return jsonify({"error": "Frontend files not found"}), 404
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=app.config['FLASK_ENV'] == 'development')
