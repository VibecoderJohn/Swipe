from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import Config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .routes import bp as api_bp
from .extensions import mongo  # import the unbound instance

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Sentry integration
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )

    mongo.init_app(app)
    jwt = JWTManager(app)
    CORS(app)

    # Health check / root route
    @app.route('/')
    def health():
        return {"status": "BioSecurePay API is running!"}, 200

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app

# For gunicorn or python app.py
app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config['FLASK_ENV'] == 'development')
