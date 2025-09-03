import os

class Config:
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-default-secret-key'
    DEBUG = False
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/biosecure_pay'
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
    MONO_SECRET_KEY = os.environ.get('MONO_SECRET_KEY')
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'production'
