from flask import Flask
from extensions import db, login_manager  # Import from the new extensions module
from flask_migrate import Migrate
from blueprints.accounts.routes import accounts_blueprint, home
from dotenv import load_dotenv
import os
from sqlalchemy import text
import threading
import time



load_dotenv()


# def create_app():
app = Flask(__name__, instance_relative_config=True)


# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL', "sqlite:///fallback.db")
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
login_manager.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
# Function to keep database connection alive
def keep_db_alive():
    with app.app_context():
        while True:
            try:
                with db.engine.connect() as conn:  # Use db.engine instead of creating a new one
                    conn.execute(text("SELECT 1"))
                    print('connection made')
            except Exception as e:
                print(f"Database keep-alive failed: {e}")
            time.sleep(600)  # Run every 10 minutes

# Start the keep-alive thread
threading.Thread(target=keep_db_alive, daemon=True).start()

# Serve static files
app.static_folder = 'static'

# return app

if __name__ == "__main__":
    # app = create_app()
    app.run(debug=True)
