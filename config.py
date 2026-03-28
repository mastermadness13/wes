import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret')
    DATABASE = os.path.join(BASE_DIR, 'data.db')
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
