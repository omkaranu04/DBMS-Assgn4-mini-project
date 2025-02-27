from . import db

class SystemUsersTop(db.Model):
    __tablename__ = 'system_users_top'
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)

class PanchayatUsers(db.Model):
    __tablename__ = 'panchayat_users'
    username = db.Column(db.String(50), primary_key=True)
    aadhar_no = db.Column(db.String(12), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(50), nullable=False)

class Citizens(db.Model):
    __tablename__ = 'citizens'
    aadhar_no = db.Column(db.String(12), primary_key=True)
    phone_no = db.Column(db.String(15))