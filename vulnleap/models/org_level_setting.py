from . import db

class OrgLevelSetting(db.Model):
    __tablename__ = 'org_level_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    last_modified_by = db.Column(db.Integer, nullable=False)
