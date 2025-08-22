from datetime import datetime
from . import db

class ActiveMortgage(db.Model):
    __tablename__ = 'active_mortgages'

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('mortgage_quotes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_balance = db.Column(db.Numeric(15,2), nullable=False)
    payment_account_number = db.Column(db.String(50))
    payment_routing_number = db.Column(db.String(50))
    next_payment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quote = db.relationship('MortgageQuote', backref=db.backref('active_mortgages', lazy=True))
    user = db.relationship('User', backref=db.backref('active_mortgages', lazy=True))

    def __repr__(self):
        return f'<ActiveMortgage {self.id}>' 