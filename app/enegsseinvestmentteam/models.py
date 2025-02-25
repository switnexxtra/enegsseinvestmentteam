from datetime import datetime
from extensions import db, login_manager  # Import db from extensions
from flask_login import UserMixin  # Import UserMixin from flask_login
from werkzeug.security import generate_password_hash, check_password_hash
import json


# User model
class User(db.Model):
    __tablename__ = 'users'  # Ensure this is set correctly

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # Added username field
    email = db.Column(db.String(120), unique=True, nullable=True)    # Email address
    country = db.Column(db.String(100), nullable=False)               # Country field
    mobile = db.Column(db.String(15), unique=True, nullable=True)    # Mobile phone number
    password_hash = db.Column(db.String(255), nullable=False) # Password hash for security
    is_admin = db.Column(db.Boolean, default=False)
    acc_balance = db.Column(db.Float, default=0.0)
    total_investment = db.Column(db.Float, default=0.0)
    monthly_return = db.Column(db.Float, default=0.0)
    withdrawn_balance = db.Column(db.Float, default=0.0)  # New field to track withdrawn balance
    transaction_history = db.Column(db.Text, nullable=True)  # This could be a JSON string or text

    # Relationship with PaymentMethod
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login requires these properties/methods:
    @property
    def is_active(self):
        return True  # Set this to False if you want to disable the user

    @property
    def is_authenticated(self):
        return True  # Return True if the user is logged in

    @property
    def is_anonymous(self):
        return False  # Return False since this is a real user

    # Add get_id method required by Flask-Login
    def get_id(self):
        return str(self.id)

    def add_transaction(self, transaction_details):
        """Append a new transaction to the transaction history."""
        transactions = json.loads(self.transaction_history) if self.transaction_history else []
        transactions.append(transaction_details)
        self.transaction_history = json.dumps(transactions)

    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # Either 'bank' or 'crypto'
    recipient_details = db.Column(db.String(255), nullable=False)  # Bank details or crypto wallet address
    transaction_status = db.Column(db.String(20), default='pending')  # Status: 'pending', 'completed', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='transactions', lazy=True)

    def __init__(self, user_id, amount, payment_method, recipient_details, transaction_status='pending'):
        self.user_id = user_id
        self.amount = amount
        self.payment_method = payment_method
        self.recipient_details = recipient_details
        self.transaction_status = transaction_status

# Payment method model
class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key linking to users
    method_type = db.Column(db.String(50), nullable=False)  # Bank Transfer or Cryptocurrency
    account_number = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    account_name = db.Column(db.String(100), nullable=True)
    sub_type = db.Column(db.String(50), nullable=True)  # USDT, BTC, etc.
    wallet_address = db.Column(db.String(255), nullable=True)
    memo = db.Column(db.String(255), nullable=True)
    network_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PaymentMethod {self.id} for User {self.user_id}>'



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Ensure correct table name
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# class SiteB(db.Model):
#     __tablename__ = 'site_b'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     acc_balance = db.Column(db.Float, default=0.0)

#     user = db.relationship('User', backref='site_b', lazy=True)
