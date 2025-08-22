import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .models import db
import uuid

def create_app():
    app = Flask(__name__)
    
    # Build database URI
    db_uri = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure SSL if specified
    ssl_mode = os.getenv('MYSQL_SSL_MODE')
    if ssl_mode and ssl_mode.upper() != 'DISABLED':
        # Only configure SSL if it's not explicitly disabled
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {
                'ssl': {'ssl_mode': ssl_mode}
            }
        }
    
    # Use a secure, persistent secret key from environment variable
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        # Generate a cryptographically secure secret key if not provided
        import secrets
        secret_key = secrets.token_hex(32)
        print("WARNING: No SECRET_KEY environment variable set. Using generated key:", secret_key)
        print("Please set SECRET_KEY environment variable with this value for production")
    app.config['SECRET_KEY'] = secret_key

    # Enable CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    db.init_app(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Force HTTPS (comment out if not using HTTPS)
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    from .routes import main
    app.register_blueprint(main)
    return app