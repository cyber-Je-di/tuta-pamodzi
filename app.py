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
    """Create and configure an instance of the Flask application.

    This function acts as an application factory. It sets up the configuration,
    initializes extensions (like the database and login manager), registers
    blueprints for routing, and ensures the database is created with initial
    data before returning the application instance.

    Returns:
        Flask: The configured Flask application object.
    """
    # ------------------------------------------------------------------
    # 1. APP CONFIGURATION
    # ------------------------------------------------------------------
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_secret_key_for_dev_only')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tuta_pamodzi.db' 
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
        """Load a user from the database given a user_id.

        This function is used by Flask-Login to manage user sessions. It takes a
        user ID from the session and returns the corresponding user object.

        Args:
            user_id (str): The ID of the user to load.

        Returns:
            User: The user object corresponding to the given ID, or None if not found.
        """
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
    """Seed the database with initial data if it's empty.

    This function checks for the existence of essential data and creates it if
    it's missing. It performs the following actions:
    1. Initializes the system settings, setting a default commission rate.
    2. Populates the database with a predefined list of universities.
    3. Creates a default administrator user for initial setup and access.

    This ensures the application has the necessary data to run correctly after
    the first setup.
    """
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
            email='admin@highexecellenceacademy.com',
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