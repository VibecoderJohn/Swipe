from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from .config import Config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .routes import bp as api_bp

app = Flask(__name__)
app.config.from_object(Config)

if app.config.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

mongo = PyMongo(app)  # This is now exported for models.py
jwt = JWTManager(app)
CORS(app)

app.register_blueprint(api_bp, url_prefix='/api/v1')

if __name__ == '__main__':
    app.run(debug=app.config['FLASK_ENV'] == 'development')

# Export mongo for models.py import
# models.py will use: from .app import mongo
