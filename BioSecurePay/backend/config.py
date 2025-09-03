import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGO_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    MONO_SECRET_KEY = os.getenv('MONO_SECRET_KEY')
    SENTRY_DSN = os.getenv('SENTRY_DSN')
