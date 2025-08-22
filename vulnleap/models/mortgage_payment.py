from . import db
from datetime import datetime

class MortgagePayment(db.Model):
    __tablename__ = 'mortgage_payments'

    id = db.Column(db.Integer, primary_key=True)
    mortgage_id = db.Column(db.Integer, db.ForeignKey('active_mortgages.id'), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('pending', 'completed', 'failed', name='payment_status_enum'), nullable=False)
    transaction_id = db.Column(db.String(100))

    mortgage = db.relationship('ActiveMortgage', backref=db.backref('mortgage_payments', lazy=True))

    def __repr__(self):
        return f'<MortgagePayment {self.id}>' 