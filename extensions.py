"""Initialize Flask extensions.

This file is used to instantiate Flask extensions to avoid circular import
issues. The extensions are initialized here without being attached to a Flask
app instance. The app is attached to the extensions in the app factory
function in `app.py`.

Attributes:
    db (SQLAlchemy): The SQLAlchemy database instance.
    login_manager (LoginManager): The Flask-Login manager instance.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions without an app yet
db = SQLAlchemy()
login_manager = LoginManager()
