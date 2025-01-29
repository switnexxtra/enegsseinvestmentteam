from flask import Flask
from .extensions import db  # Import from the new extensions module
from flask_migrate import Migrate
from blueprints.accounts.routes import accounts_blueprint, home
from dotenv import load_dotenv
import os


load_dotenv()


# def create_app():
app = Flask(__name__, instance_relative_config=True)

# app.config['SQLALCHEMY_DATABASE_URI'] = ''
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SECRET_KEY'] = '@Enegssei123-5investmentteam808092BuilD'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Security settings
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configurations (if using instance folder)
app.config.from_pyfile('config.py', silent=True)



# Register blueprints
app.register_blueprint(home, url_prefix='/')
app.register_blueprint(accounts_blueprint, url_prefix='/accounts')


# Initialize the database and migration
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# Serve static files
app.static_folder = 'static'

# return app

if __name__ == "__main__":
    # app = create_app()
    app.run(debug=True)
