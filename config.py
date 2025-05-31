import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_key_for_dev')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:////home/keisyavalencia03/codeboom/instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False