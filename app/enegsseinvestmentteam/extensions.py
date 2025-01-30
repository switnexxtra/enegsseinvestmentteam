from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


# Initialize SQLAlchemy
db = SQLAlchemy()


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "accounts.login"  # Redirect unauthorized users to login
