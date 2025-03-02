from . import db

# System Users (System Administrators and Government Officials)
class SystemUsersTop(db.Model):
    __tablename__ = 'system_users_top'
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # e.g., 'System Administrator', 'Government Official'

# Panchayat Employees
class PanchayatUsers(db.Model):
    __tablename__ = 'panchayat_users'
    username = db.Column(db.String(50), primary_key=True)
    aadhar_no = db.Column(db.String(12), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(50), nullable=False)  # e.g., 'Sarpanch', 'Naib Sarpanch'

# Citizens
class Citizens(db.Model):
    __tablename__ = 'citizens'
    aadhar_no = db.Column(db.String(12), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)  # Date of Birth
    gender = db.Column(db.String(10), nullable=False)  # e.g., 'Male', 'Female'
    house_no = db.Column(db.Integer, db.ForeignKey('household.house_no'))
    phone_no = db.Column(db.String(15))
    email_id = db.Column(db.String(100))
    education_level = db.Column(
        db.String(20),
        nullable=False,
        default='Uneducated'
    )  # e.g., 'Uneducated', 'High School', 'Graduate','Post Graduate','Secondary'
    income = db.Column(db.Numeric, default=0.0)
    employment = db.Column(
        db.String(20),
        nullable=False,
        default='Unemployed'
    )  # e.g., 'Unemployed', 'Employee', 'Self-Employee','Business'
    is_alive = db.Column(db.Boolean, default=True)

# Household
class Household(db.Model):
    __tablename__ = 'household'
    house_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    address = db.Column(db.Text, nullable=False)

# Taxation
class Taxation(db.Model):
    __tablename__ = 'taxation'
    aadhar_no = db.Column(
        db.String(12), 
        db.ForeignKey('citizens.aadhar_no'), 
        primary_key=True
    )
    tax_amount = db.Column(db.Numeric, nullable=False, default=0.0)
    payment_status = db.Column(db.Boolean, default=False)

# Certificates
class Certificates(db.Model):
    __tablename__ = 'certificates'
    certificate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aadhar_no = db.Column(
        db.String(12), 
        db.ForeignKey('citizens.aadhar_no'), 
        nullable=False
    )
    certificate_type = db.Column(
        db.String(20),
        nullable=False
    )  # e.g., 'Birth', 'Death', 'Caste', 'Domicille', 'Residence', 'Character'
    date_of_issue = db.Column(db.Date, nullable=False)

# Welfare Schemes
class Welfare_Schemes(db.Model):
    __tablename__ = 'welfare_schemes'
    scheme_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scheme_type = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Numeric, nullable=False)
    scheme_description = db.Column(db.Text)

# Avails (Welfare Scheme Beneficiaries)
class Avails(db.Model):
    __tablename__ = 'avails'
    aadhar_no = db.Column(
        db.String(12),
        db.ForeignKey('citizens.aadhar_no'),
        primary_key=True
    )
    scheme_id = db.Column(
        db.Integer,
        db.ForeignKey('welfare_schemes.scheme_id'),
        primary_key=True
    )
    avail_date = db.Column(db.Date, nullable=False)

# Agricultural Land
class Agricultural_Land(db.Model):
    __tablename__ = 'agricultural_land'
    land_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aadhar_no = db.Column(
        db.String(12),
        db.ForeignKey('citizens.aadhar_no'),
        nullable=False
    )
    area_in_acres = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )  # Minimum 1 acre
    crop_type = db.Column(
        db.String(20),
        nullable=False
    )  # e.g., 'Rice', 'Wheat', etc.
    soil_type = db.Column(
        db.String(20),
        nullable=False,
        default='Alluvial'
    )  # e.g., 'Alluvial', 'Black'

# Health Check-Up Records
class Health_CheckUp(db.Model):
    __tablename__ = 'health_checkup'
    checkup_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aadhar_no = db.Column(
        db.String(12),
        db.ForeignKey('citizens.aadhar_no'),
        nullable=False
    )
    medical_condition = db.Column(
        db.Text,
        nullable=False
    )  # Description of the condition/disease
    prescription = db.Column(
        db.Text,
        nullable=True
    )  # Optional prescription details
    date_of_visit = db.Column(
        db.Date,
        nullable=False
    )

# Resources (Infrastructure like Roads, Water Supply, etc.)
class Resources(db.Model):
    __tablename__ = 'resources'
    resource_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_name = db.Column(
        db.String(20),
        nullable=False
    )  # e.g., 'Road', 'Water', 'Drainage System'
    last_inspected_date = db.Column(db.Date, nullable=True)

# Complaints (Related to Resources)
class Complaints(db.Model):
    __tablename__ = 'complaints'
    complaint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_id = db.Column(
        db.Integer,
        db.ForeignKey('resources.resource_id'),
        nullable=False
    )
    aadhar_no = db.Column(
        db.String(12),
        db.ForeignKey('citizens.aadhar_no'),
        nullable=False
    )
    complaint_desc = db.Column(db.Text, nullable=False)  # Description of the complaint
    complain_date = db.Column(db.Date, nullable=False)  # Date of filing the complaint

# Meetings (Panchayat Meetings)
class Meetings(db.Model):
    __tablename__ = 'meetings'
    meeting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_conducted = db.Column(db.Date, nullable=False)  # Date of the meeting
    meeting_agenda = db.Column(db.Text, nullable=False)  # Agenda of the meeting

# Government Institutions (e.g., Education, Health, Banking)
class Government_Institutions(db.Model):
    __tablename__ = 'government_institutions'
    institute_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    institute_type = db.Column(
        db.String(20),
        nullable=False
    )  # e.g., 'Educational', 'Health', 'Banking', 'Administrative'
    institute_name = db.Column(db.String(100), nullable=False)  # Name of the institution
    institute_location = db.Column(db.Text, nullable=False)  # Address/location of the institution