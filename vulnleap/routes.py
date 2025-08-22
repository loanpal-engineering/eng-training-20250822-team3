from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from vulnleap.models.mortgage_quote import MortgageQuote
from vulnleap.models import db, User, Session, OrgLevelSetting
import bcrypt
import random
import uuid
import re
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

# Generate a random interest rate between 2.5% and 5.5%
interest_rate = round(random.uniform(2.5, 5.5), 2)

def is_valid_number(value):
    # Check for any case of 'nan' and ensure it's a valid number
    if isinstance(value, str) and value.strip().lower() == 'nan':
        return False
    # Check if value is a valid int or float string
    return re.match(r'^-?\d+(\.\d+)?$', value.strip()) is not None

def is_nan_str(val):
    return isinstance(val, str) and val.strip().lower() == 'nan'

def safe_int(val):
    if is_nan_str(val):
        return None
    try:
        return int(val)
    except Exception:
        return None

def safe_float(val):
    if is_nan_str(val):
        return None
    try:
        return float(val)
    except Exception:
        return None

def validate_session():
    """Validate user session against database and check expiration"""
    if 'user_id' not in session or 'session_token' not in session:
        return None
    
    # Check if session exists in database and is not expired
    db_session = Session.query.filter_by(
        user_id=session['user_id'], 
        session_token=session['session_token']
    ).first()
    
    if not db_session:
        # Session not found in database, clear session
        session.clear()
        return None
    
    # Check if session is older than 24 hours
    if db_session.created_at < datetime.utcnow() - timedelta(hours=24):
        # Session expired, remove from database and clear session
        db.session.delete(db_session)
        db.session.commit()
        session.clear()
        return None
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        # User not found, clear session
        session.clear()
        return None
    
    return user

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/quote', methods=['GET', 'POST'])
def quote():
    if request.method == 'POST':
        loan_term_str = request.form['loan_term']
        home_cost_str = request.form['home_cost']
        credit_score_str = request.form['credit_score']
        down_payment_str = request.form['down_payment']
        loan_term = safe_int(loan_term_str)
        home_cost = safe_float(home_cost_str)
        credit_score = safe_int(credit_score_str)
        down_payment = safe_float(down_payment_str)
        ssn_number = request.form['ssn_number']

        if loan_term is None or home_cost is None or credit_score is None or down_payment is None:
            flash("Invalid input: Please enter valid numbers and do not use 'NaN'.", "danger")
            return redirect(url_for('main.quote'))
        
        if down_payment > home_cost:
            flash("Down payment cannot be greater than home cost.", "danger")
            return redirect(url_for('main.quote'))
        
        if down_payment < 0:
            flash("Down payment cannot be negative.", "danger")
            return redirect(url_for('main.quote'))
        
        if home_cost < 0:
            flash("Home cost cannot be negative.", "danger")
            return redirect(url_for('main.quote'))
        
        if credit_score < 0 or credit_score > 850:
            flash("Credit score must be between 0 and 850.", "danger")
            return redirect(url_for('main.quote'))
        
        final_loan_amount = home_cost - down_payment
        # Calculate the final interest rate based on the credit score - higher credit score = lower interest rate
        final_interest_rate = interest_rate - (credit_score - 600) / 1000
        if final_interest_rate < 0.2:
            final_interest_rate = 0.2  # Set a minimum interest rate
        monthly_interest_rate = final_interest_rate / 100 / 12
        num_payments = loan_term * 12

        if monthly_interest_rate == 0:
            monthly_payment = final_loan_amount / num_payments
        else:
            monthly_payment = final_loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments) / ((1 + monthly_interest_rate) ** num_payments - 1)

        quote_amount = monthly_payment * num_payments
        total_interest = quote_amount - final_loan_amount

        user_id = None
        if 'user_id' in session and session['user_id'] is not None:
            user_id = session['user_id']

        # Make a new quote object
        if user_id is not None:
            quote = MortgageQuote(property_value=home_cost, credit_score=credit_score, down_payment=down_payment, loan_amount=final_loan_amount, interest_rate=final_interest_rate, term_years=loan_term, monthly_payment=monthly_payment, status='quote', user_id=user_id, total_interest=total_interest, ssn_number=ssn_number)
        else:
            quote = MortgageQuote(property_value=home_cost, credit_score=credit_score, down_payment=down_payment, loan_amount=final_loan_amount, interest_rate=final_interest_rate, term_years=loan_term, monthly_payment=monthly_payment, status='quote', total_interest=total_interest, ssn_number=ssn_number)
        db.session.add(quote)
        db.session.commit()

        return render_template('quote.html',
                               interest_rate=interest_rate,
                               quote_amount=quote_amount,
                               monthly_payment=monthly_payment,
                               total_interest=total_interest,
                               loan_term=loan_term,
                               quote_id=quote.id)
    return render_template('quote.html', interest_rate=interest_rate)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session and session['user_id'] is not None:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template('register.html', username=username)
        
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        quote_id = None
        if 'quote_id' in request.form:
            quote_id = request.form['quote_id']

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', username=username)
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "danger")
            return render_template('register.html', username=username)
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new user object
        user = User(username=username, password_hash=hashed_password, user_type=role)
        db.session.add(user)
        db.session.commit()

        if quote_id:
            quote = MortgageQuote.query.get(quote_id)
            quote.user_id = user.id
            db.session.commit()

        # Create a flask session
        session['user_id'] = user.id
        session['username'] = user.username
        session['user_type'] = user.user_type
        session['session_token'] = str(uuid.uuid4())
        session.permanent = True
        db.session.add(Session(user_id=user.id, session_token=session['session_token']))

        return redirect(url_for('main.index'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    if 'user_id' in session and session['user_id'] is not None:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Invalid username.", "danger")
            return redirect(url_for('main.login'))
        
        # Ensure password_hash is bytes for bcrypt
        password_hash = user.password_hash
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        # Check if the password is correct
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
            flash("Invalid password.", "danger")
            return redirect(url_for('main.login'))
        
        # Create a flask session
        session['user_id'] = user.id
        session['username'] = user.username
        session['user_type'] = user.user_type
        session['session_token'] = str(uuid.uuid4())
        session.permanent = True
        db.session.add(Session(user_id=user.id, session_token=session['session_token']))

        return redirect(url_for('main.index'))
    return render_template('login.html')

@main.route('/logout')
def logout():
    # Clean up database session if exists
    if 'user_id' in session and 'session_token' in session:
        db_session = Session.query.filter_by(
            user_id=session['user_id'], 
            session_token=session['session_token']
        ).first()
        if db_session:
            db.session.delete(db_session)
            db.session.commit()
    
    # Clear Flask session
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('main.index'))

@main.route('/user', methods=['GET', 'POST'])
def user():
    if request.method == 'POST':
        user = validate_session()
        if not user:
            flash("You must be logged in to access this page.", "danger")
            return redirect(url_for('main.login'))
        
        if "password" in request.form:
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('main.user'))
            
            # Validate password strength
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, "danger")
                return redirect(url_for('main.user'))
            
            user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for('main.user'))
    quotes = MortgageQuote.query.filter_by(user_id=session['user_id']).all()
    return render_template('user_page.html', quotes=quotes)

@main.route('/quote/<int:quote_id>')
def quote_page(quote_id):
    user = validate_session()
    if not user:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for('main.login'))

    quote = MortgageQuote.query.get(quote_id)
    if not quote:
        flash("Quote not found.", "danger")
        return redirect(url_for('main.user'))
    
    # SECURITY FIX: Check if user owns this quote or is admin
    if quote.user_id != user.id and user.user_type not in ['admin', 'superadmin']:
        flash("You do not have permission to view this quote.", "danger")
        return redirect(url_for('main.user'))
    
    return render_template('existing_quote.html', quote=quote)

@main.route('/admin')
def admin():
    if 'user_id' not in session or session['user_id'] is None:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('main.login'))
    
    # Check if the user is an admin
    if user.user_type != 'superadmin' and user.user_type != 'admin':
        flash("You do not have access to this page.", "danger")
        return redirect(url_for('main.index'))
    

    # Get a list of all users and their roles
    users = User.query.all()
    user_roles = {}
    for user in users:
        user_roles[user.id] = user.user_type

    # Get a list of all quotes and their user ids
    quotes = MortgageQuote.query.all()
    quote_users = {}
    for quote in quotes:
        quote_users[quote.id] = quote.user_id
    
    return render_template('admin.html', user=user, users=users, user_roles=user_roles, quotes=quotes, quote_users=quote_users)


@main.route('/orgadmin')
def orgadmin():
    if 'user_id' not in session or session['user_id'] is None:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('main.login'))
    
    # Check if the user is an org admin
    if user.user_type != 'superadmin':
        flash("You do not have access to this page.", "danger")
        return redirect(url_for('main.index'))
    
    # Functionality to add new admins and superadmins
    if request.method == 'POST':
        # Check if this is a new user creation or a setting change
        if 'username' in request.form:
            # New user creation
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            role = request.form['role']
                    
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('main.orgadmin'))
            
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create a new user object
            new_user = User(username=username, password_hash=hashed_password, user_type=role)
            db.session.add(new_user)
            db.session.commit()
            flash("User created successfully.", "success")
            return redirect(url_for('main.orgadmin'))
        else:
            # Setting change
            setting_key = request.form['setting_key']
            setting_value = request.form['setting_value']
            
            # Create a new org level setting object
            new_setting = OrgLevelSetting(setting_key=setting_key, setting_value=setting_value, last_modified_by=user.id)
            db.session.add(new_setting)
            db.session.commit()
            flash("Setting updated successfully.", "success")
            return redirect(url_for('main.orgadmin'))
    
    # Get all org level settings for the current org
    org_settings = OrgLevelSetting.query.all()
    return render_template('orgadmin.html', user=user, org_settings=org_settings)