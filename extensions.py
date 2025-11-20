# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions without an app yet
db = SQLAlchemy()
login_manager = LoginManager()