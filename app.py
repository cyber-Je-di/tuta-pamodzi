# app.py
import os
from flask import Flask, redirect, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

# Import extensions (db and login_manager) from the new extensions file
from extensions import db, login_manager 

# We import the models file so SQLAlchemy registers the classes, but we don't import the classes themselves
import models 
# Import specific classes needed only for initialization functions
from models import User, University, SystemSetting, ROLES 


def create_app():
    # ------------------------------------------------------------------
    # 1. APP CONFIGURATION
    # ------------------------------------------------------------------
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_secret_key_for_dev_only')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tuta_pamoja.db' 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
    app.config['UPLOAD_FOLDER'] = 'documents' 
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


    # ------------------------------------------------------------------
    # 2. EXTENSION INITIALIZATION
    # ------------------------------------------------------------------
    # Attach the extensions to the app instance here
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' 

    # ------------------------------------------------------------------
    # 3. USER LOADER
    # ------------------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        # User model is available because we imported models at the top
        return db.session.get(User, int(user_id))

    # ------------------------------------------------------------------
    # 4. BLUEPRINTS (For organizing routes)
    # ------------------------------------------------------------------
    
    #1. Import and register the main Blueprint containing landing, login, register, and student dashboard
    from main_routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Note: Placeholder routes removed as 'main' blueprint handles '/' and others.
    # 2. Register the tutor Blueprint
    from tutor_routes import tutor as tutor_blueprint
    app.register_blueprint(tutor_blueprint)
    
    # 3. Register the Admin Blueprint  <-- NEW LINES
    from admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    # ------------------------------------------------------------------
    # 5. DATABASE SETUP AND INITIAL DATA (Run once)
    # ------------------------------------------------------------------
    with app.app_context():
        # db.create_all() works because all models are imported via 'import models'
        db.create_all() 
        initialize_data()

    return app

def initialize_data():
    """Initializes the Universities and a default Admin user if they don't exist."""
    
    # 1. Check/Set System Settings (Commission Rate)
    if not db.session.get(SystemSetting, 1):
        db.session.add(SystemSetting(id=1, commission_rate=0.10))
        print("Initialized SystemSetting (10% commission)")
    
    # 2. Add Universities (Requirement 1.2.1)
    universities_list = ['UNZA', 'CBU', 'MU', 'ZICAS', 'Cavendish']
    for name in universities_list:
        if not db.session.scalar(db.select(University).filter_by(name=name)):
            db.session.add(University(name=name))
            print(f"Added University: {name}")

    # 3. Add Default Admin User (For initial access and testing)
    admin_username = 'admin'
    if not db.session.scalar(db.select(User).filter_by(username=admin_username)):
        admin_user = User(
            username=admin_username,
            full_name='Lead Administrator',
            email='admin@tutapamoja.com',
            role=ROLES['Admin']
        )
        admin_user.set_password('supersecurepassword123') 
        db.session.add(admin_user)
        print("Added default Admin user.")

    db.session.commit()
    print("Database initialization complete.")


# This part runs the application when you execute `python app.py`
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)