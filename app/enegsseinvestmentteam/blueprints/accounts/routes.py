from datetime import datetime
import os
from flask import Blueprint, render_template, session
import random
import psycopg2
from sqlalchemy.exc import OperationalError
from flask import render_template, request, url_for, redirect, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user  # Assuming you're using Flask-Login for user sessions
from extensions import login_manager  # Import from the new extensions module
from models import db, User, Transaction, PaymentMethod, load_user  # Assuming your models are in a `models.py` file



accounts_blueprint = Blueprint('accounts', __name__, static_folder='static', template_folder='templates')
home = Blueprint('home', __name__, static_folder='static', template_folder='templates')


# conn = psycopg2.connect(database="postgres", host="localhost", user="", password="", port="5432")
# cur = conn.cursor()

@home.route('/')
def index():
    return render_template('accounts/login.html')

# Hardcoded credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

@accounts_blueprint.errorhandler(OperationalError)
def handle_db_error(e):
    flash("Sorry an error occurred. Please refresh and try again.", "error")
    return jsonify({"error": "Sorry an error occurred. Please refresh and try again."}), 500


@accounts_blueprint.route('/user/register', methods=['GET', 'POST'])
def register():
    return render_template('accounts/register.html')


# @accounts_blueprint.route('/user/register_user', methods=['GET', 'POST'])
# def register_user():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         country = request.form['country']
#         mobile = request.form['mobile']
#         password = request.form['password']

#         if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
#             flash('Username or email already exists!', 'danger')
#             return redirect(url_for('accounts.register_user'))

#         new_user = User(username=username, email=email, country=country, mobile=mobile, password_hash=generate_password_hash(password))
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Account created successfully! Please login.', 'success')
#         return redirect(url_for('accounts.login'))
#     return render_template('accounts/register.html')


@accounts_blueprint.route('/user/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email')  # Use `.get()` to handle missing input
        country = request.form['country']
        mobile = request.form['mobile']
        password = request.form['password']

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('accounts.register_user'))

        # Check if email exists ONLY IF the user provided one
        if email and User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('accounts.register_user'))

        # Create new user without requiring email
        new_user = User(
            username=username, 
            email=email if email else None,  # Store None if no email is provided
            country=country, 
            mobile=mobile, 
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('accounts.login'))

    return render_template('accounts/register.html')


@accounts_blueprint.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Redirect admin users to the admin dashboard
            if user.is_admin:
                return redirect(url_for('accounts.admin_dashboard'))  # Replace with the correct route
            
            flash('Login successful!', 'success')
            return redirect(url_for('accounts.user_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('accounts.login'))
        
    # Render login form for GET requests
    return render_template('accounts/login.html')

# @accounts_blueprint.route('/user/login', methods=['GET', 'POST'])
# def login():
#     try:
#         if request.method == 'POST':
#             username = request.form['username']
#             password = request.form['password']
#             user = User.query.filter_by(username=username).first()
            
#             if user and user.check_password(password):
#                 login_user(user)
#                 flash('Login successful!', 'success')

#                 # Redirect admin users to the admin dashboard
#                 if user.is_admin:
#                     return redirect(url_for('admin.admin_dashboard'))  # Replace with the correct route

#                 # Redirect regular users to their dashboard
#                 return redirect(url_for('accounts.user_dashboard'))
#             else:
#                 flash('Invalid username or password!', 'danger')
#                 return redirect(url_for('accounts.login'))
#     except Exception as e:
#         flash(f"An error occurred: {e}", "danger")
#         return redirect(url_for('accounts.login'))  # Redirect to login in case of an error


@accounts_blueprint.route('/user-dashboard')
@login_required
def user_dashboard():
    # Retrieve the logged-in user's ID from the session
    # user_id = session.get('user_id')
    # user = current_user  # Flask-Login handles session management
    
    # # Redirect to login if the user is not authenticated
    # if not user_id:
    #     return redirect(url_for('accounts.login'))
    
    user = current_user  # Flask-Login handles session management

    if not user.is_authenticated:  # This checks if the user is logged in
        return redirect(url_for('accounts.login'))


    user_id=user.id
    # # Query the logged-in user's data
    # user = User.query.get(user_id)

    # # Check if the user exists in the database
    # if not user:
    #     return redirect(url_for('accounts.login'))  # Additional safety check
    
    # Extract financial information
    financials = {
        'account_balance': user.acc_balance,
        'total_investments': user.total_investment,
        'monthly_returns': user.monthly_return
    }
    
    # Parse the transaction history from JSON if it exists
    # Query the user's transactions
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()

    # Optional: Format transactions into a list of dicts for easier use in the template
    transaction_data = [
        {
            "date": t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "description": f"Payment via {t.payment_method}",
            "amount": t.amount,
            "status": t.transaction_status
        }
        for t in transactions
    ]
    
    # Fetch payment methods from the database
    payment_methods = PaymentMethod.query.all()
    
    # Filter payment methods into two categories: Bank Transfer and Crypto
    # bank_methods = [method for method in payment_methods if method.method_type == 'Bank Transfer']
    bank_methods = [method for method in payment_methods if method.method_type == 'Bank Transfer']
    crypto_methods = [method for method in payment_methods if method.method_type == 'Cryptocurrency']
    # print("Bank Transfer Methods:")
    # for method in bank_methods:
    #     print(f"- {method.method_type}: {method.bank_name}, {method.account_number}")

    # print("\nCryptocurrency Methods:")
    # for method in crypto_methods:
    #     print(f"- {method.method_type}: {method.sub_type}")

    
    # Filter crypto methods by 'sub_type' (BTC or USDT)
    btc_methods = [method for method in crypto_methods if method.sub_type == 'BTC']
    usdt_methods = [method for method in crypto_methods if method.sub_type == 'USDT']
    
    # Prepare the data to pass to the template
    payment_data = {
        'bank_method': random.choice(bank_methods) if bank_methods else None,  # Randomly select one bank method
        'btc_method': random.choice(btc_methods) if btc_methods else None,  # Randomly select one BTC method
        'usdt_method': random.choice(usdt_methods) if usdt_methods else None,  # Randomly select one USDT method
    }

    return render_template('accounts/users.html', financials=financials, transactions=transaction_data, payment_data=payment_data, user_id=user_id)

    
@accounts_blueprint.route('/new_transaction', methods=['POST'])
def add_new_transaction():
    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    recipient_details = request.form.get('recipient_details')

    print(f"Amount: {amount}, Payment Method: {payment_method}, Recipient Details: {recipient_details}")
    if not amount or not payment_method:
        flash("All fields are required!", "danger")
        return redirect(url_for('accounts.user_dashboard'))
    
    if not recipient_details:
        recipient_details = f"Payment Via: {payment_method}"
        

    # Fetch the current user's ID from session
    # user_id = session.get('user_id')
    
    # Fetch the user based on the user_id
    # user = User.query.get(user_id)
    user = current_user
    # user_id=user.id
    
    # Get the current date and time
    now = datetime.now()
    try:
        # Create a new transaction
        transaction = Transaction(
            user_id=user.id,
            amount=float(amount),
            payment_method=payment_method,
            recipient_details=recipient_details,
            transaction_status='pending',  # Mark as pending
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Transaction recorded successfully. Await verification.", "success")
    except Exception as e:
        print(e)
        db.session.rollback()
        flash("An error occurred while processing your transaction.", "danger")

    return redirect(url_for('accounts.user_dashboard'))


@accounts_blueprint.route('/withdraw', methods=['POST'])
def withdraw():
    # Get data from the form
    account_name = request.form.get('accountName')
    account_number = request.form.get('accountNumber')
    bank_name = request.form.get('bankName')
    withdraw_amount = request.form.get('withdrawAmount')

    # Check if withdraw_amount is not None and convert it to float
    if withdraw_amount is not None:
        withdraw_amount = float(withdraw_amount)
    else:
        flash("Withdrawal amount is required.", "danger")
        return redirect(url_for('accounts.withdraw'))

    # Fetch the current user's ID from session
    user = current_user
    user_id = user.id

    if not user_id:
        flash("You need to log in first.", "danger")
        return redirect(url_for('accounts.login'))

    # Fetch the user based on the user_id
    # user = User.query.get(user_id)
    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for('accounts.login'))

    # Check if the withdrawal amount is valid (less than or equal to the balance)
    if withdraw_amount <= user.acc_balance:
        # Create a new transaction
        new_transaction = Transaction(
            user_id=user.id,
            amount=withdraw_amount,
            payment_method='bank',  # Assuming bank is the payment method for withdrawals
            recipient_details=f"Account Name: {account_name}, Account Number: {account_number}, Bank Name: {bank_name}"
        )
        
        # Update the user's account balance
        user.acc_balance -= withdraw_amount
        
        # Add the transaction to the database
        db.session.add(new_transaction)
        db.session.commit()
        
        # Add transaction history to the User model (optional)
        user.add_transaction({
            'transaction_type': 'withdrawal',
            'amount': withdraw_amount,
            'status': 'completed',
            'recipient_details': f"{account_name}, {account_number}, {bank_name}"
        })
        db.session.commit()

        flash("Withdrawal successfully processed!", "success")
    else:
        flash("Insufficient balance to withdraw this amount. you need to deposit first", "danger")

    return redirect(url_for('accounts.user_dashboard'))  # Redirect to the dashboard or any other page


@accounts_blueprint.route('/profile', methods=['GET'])
@login_required
def profile():
    user = current_user
    user_id = user.id
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

   
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'first_name': user.username,  # Replace with actual field if different
        'last_name': user.country,    # Replace with actual field if different
        'email': user.email,
        'phone': user.mobile
    })


@accounts_blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have successfully logged out.", "success")
    return redirect(url_for('accounts.login'))

@accounts_blueprint.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    # Fetch all users from the database
    users = User.query.all()
    
    # Fetch all payment methods from the database
    payment_methods = PaymentMethod.query.all()

    # Fetch all transactions from the database
    transactions = Transaction.query.all()

    return render_template('accounts/admin_dashboard.html', users=users, payment_methods=payment_methods, transactions=transactions)



@accounts_blueprint.route('/add_payment_method', methods=['GET', 'POST'])
@login_required
def add_payment_method():
    if request.method == 'POST':
        method_type = request.form.get('method_type')
        
        # Get the logged-in user's ID (using session or Flask-Login)
        user_id = session.get('user_id')  # Assuming user_id is stored in session
        # Get the logged-in user's ID
        user_id = current_user.id  # Flask-Login provides `current_user`
        if not user_id:
            flash('You must be logged in to add a payment method.', 'error')
            return redirect('accounts.login')

        # Conditional fields
        if method_type == 'Bank Transfer':
            account_number = request.form.get('account_number')
            bank_name = request.form.get('bank_name')
            account_name = request.form.get('account_name')
            sub_type = wallet_address = memo = network_address = None
        elif method_type == 'Cryptocurrency':
            account_number = bank_name = account_name = None
            sub_type = request.form.get('sub_type')
            wallet_address = request.form.get('wallet_address')
            memo = request.form.get('memo')
            network_address = request.form.get('network_address')
        else:
            flash('Invalid payment method type selected!', 'error')
            return redirect('accounts.admin_dashboard')

        # Save to database
        payment_method = PaymentMethod(
            user_id=user_id,  # Associate the payment method with the logged-in user
            method_type=method_type,
            account_number=account_number,
            bank_name=bank_name,
            account_name=account_name,
            sub_type=sub_type,
            wallet_address=wallet_address,
            memo=memo,
            network_address=network_address
        )
        db.session.add(payment_method)
        db.session.commit()
        flash('Payment method added successfully!', 'success')
        return redirect(url_for('accounts.admin_dashboard'))

    return render_template('accounts/admin_dashboard.html')

@accounts_blueprint.route('/edit-payment-method', methods=['POST'])
def edit_payment_method():
    method_id = request.form.get('method_id')
    payment_method = PaymentMethod.query.get(method_id)

    if payment_method:
        payment_method.method_type = request.form.get('method_type')
        payment_method.account_number = request.form.get('account_number')
        payment_method.bank_name = request.form.get('bank_name')
        payment_method.account_name = request.form.get('account_name')
        payment_method.wallet_address = request.form.get('wallet_address')
        payment_method.memo = request.form.get('memo')
        payment_method.network_address = request.form.get('network_address')
        db.session.commit()
        flash('Payment method updated successfully!', 'success')
    else:
        flash('Payment method not found!', 'error')

    return redirect(url_for('accounts.admin_dashboard'))



@accounts_blueprint.route('/delete-payment-method/<int:method_id>', methods=['POST'])
def delete_payment_method(method_id):
    payment_method = PaymentMethod.query.get(method_id)

    if payment_method:
        db.session.delete(payment_method)
        db.session.commit()
        flash('Payment method deleted successfully!', 'success')
    else:
        flash('Payment method not found!', 'error')

    return redirect(url_for('accounts.admin_dashboard'))




from flask import request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
@accounts_blueprint.route('/edit_transaction', methods=['POST'])
def edit_transaction():
    
    try:
        # Get the data from the form
        user_id = request.form.get('user_id')
        transaction_id = request.form.get('transaction_id')
        acc_balance = float(request.form.get('acc_balance'))
        total_investment = float(request.form.get('total_investment'))
        monthly_return = float(request.form.get('monthly_return'))
        transaction_status = request.form.get('transaction_status')

        # Find the user and the transaction
        user = User.query.get(user_id)
        transaction = Transaction.query.get(transaction_id)

        if not user or not transaction:
            flash('User or Transaction not found', 'danger')
            return redirect(url_for('accounts.admin_dashboard'))

        # Update user balance, investment, and return
        user.acc_balance = acc_balance
        user.total_investment = total_investment
        user.monthly_return = monthly_return

        # Update the transaction status
        transaction.transaction_status = transaction_status

        # Commit the changes to the database
        db.session.commit()

        flash('Transaction and user details updated successfully', 'success')
        return redirect(url_for('accounts.admin_dashboard'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred while updating the transaction. Please try again.', 'danger')
        return redirect(url_for('accounts.admin_dashboard'))

# @accounts_blueprint.route('/edit_transaction', methods=['POST'])
@accounts_blueprint.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    # Fetch the transaction using the transaction_id
    transaction = Transaction.query.get(transaction_id)
    
    if transaction:
        # Optionally, if you want to perform additional logic (e.g., updating user balances)
        user = transaction.user
        # For example, if needed, you can adjust the user's balances
        user.acc_balance -= transaction.amount  # Example: Subtract the amount of the transaction from the user's balance
        db.session.commit()
        
        # Delete the transaction
        db.session.delete(transaction)
        db.session.commit()

        # Flash success message
        flash('Transaction deleted successfully!', 'success')
    else:
        # Flash error message if transaction is not found
        flash('Transaction not found!', 'danger')

    # Redirect back to the transactions page
    return redirect(url_for('accounts.admin_dashboard'))



@accounts_blueprint.route('/edit_user', methods=['POST'])
def edit_user():
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)

    # Update user details
    user.acc_balance = float(request.form.get('acc_balance'))
    user.total_investment = float(request.form.get('total_investment'))
    user.monthly_return = float(request.form.get('monthly_return'))

    # Update specific transaction based on transaction_id
    transaction_id = request.form.get('transaction_id')
    if transaction_id:
        transaction = Transaction.query.get_or_404(transaction_id)
        transaction.transaction_status = request.form.get('transaction_status')
    
    db.session.commit()
    flash("User details and transaction status updated successfully!", "success")
    return redirect(url_for('accounts.admin_dashboard'))
