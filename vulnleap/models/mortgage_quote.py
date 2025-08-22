from datetime import datetime
from . import db

class MortgageQuote(db.Model):
    __tablename__ = 'mortgage_quotes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    property_value = db.Column(db.Numeric(15,2), nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    down_payment = db.Column(db.Numeric(15,2), nullable=False)
    ssn_number = db.Column(db.String(11), nullable=False)
    loan_amount = db.Column(db.Numeric(15,2), nullable=False)
    interest_rate = db.Column(db.Numeric(5,2), nullable=False)
    term_years = db.Column(db.Integer, nullable=False)
    monthly_payment = db.Column(db.Numeric(10,2), nullable=False)
    total_interest = db.Column(db.Numeric(15,2), nullable=False)
    status = db.Column(db.Enum('quote', 'in_progress', 'active', 'paid_off', 'cancelled', name='quote_status_enum'), nullable=False, default='quote')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('mortgage_quotes', lazy=True))

    def __repr__(self):
        return f'<MortgageQuote {self.id}>' 