from datetime import datetime
from . import db

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('system_settings', lazy=True))

    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>' 