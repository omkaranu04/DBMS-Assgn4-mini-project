from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response
from .forms import LoginForm, PanchayatEmployeeForm, GovernmentOfficialForm
from .models import SystemUsersTop, PanchayatUsers, Citizens, Certificates, Welfare_Schemes, Agricultural_Land, Health_CheckUp, Taxation, Meetings, Complaints, Household, Resources, Government_Institutions
from sqlalchemy import text, true
from . import db
from datetime import datetime
import re
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5

def verify_password(stored_password, input_password):
    hashed_input = md5(input_password.encode()).hexdigest()
    return stored_password == hashed_input

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()
        user_type = form.user_type.data.strip()

        # Import the hash function
        from hashlib import md5

        if user_type == 'System Administrator':
            user = SystemUsersTop.query.filter_by(username=username).first()
            
            if user and user.password == password and user.user_type == 'System Administrator':
                session['user'] = username
                session['user_type'] = 'System Administrator'
                return redirect(url_for('main.dashboard_administrator'))
            else:
                flash('Invalid credentials for System Administrator.', 'danger')
        
        elif user_type == 'Government Official':
            user = SystemUsersTop.query.filter_by(username=username).first()
            
            # Hash the input password and compare with stored hash
            hashed_password = md5(password.encode()).hexdigest()
            
            if user and user.password == hashed_password and user.user_type == 'Government Official':
                session['user'] = username
                session['user_type'] = 'Government Official'
                return redirect(url_for('main.dashboard_official'))
            else:
                flash('Invalid credentials for Government Official.', 'danger')

        elif user_type == 'Panchayat Employee':
            user = PanchayatUsers.query.filter_by(username=username).first()
            
            # Hash the input password and compare with stored hash
            hashed_password = md5(password.encode()).hexdigest()
            
            if user and user.password == hashed_password:
                session['user'] = username
                session['user_type'] = 'Panchayat Employee'
                return redirect(url_for('main.dashboard_employees'))
            else:
                flash('Invalid credentials for Panchayat Employee.', 'danger')

        elif user_type == 'Citizen':
            citizen_user = Citizens.query.filter_by(aadhar_no=username).first()
            
            if citizen_user:                                                                                            
                expected_password = f"{username[:4]}@{citizen_user.phone_no[-4:]}"
                if password == expected_password:
                    session['user'] = username
                    session['user_type'] = 'Citizen'
                    return redirect(url_for('main.citizen', aadhar_no=username))
            
            flash('Invalid credentials for Citizen.', 'danger')

        else:
            flash('Invalid User Type selected.', 'danger')

    return render_template('login.html', form=form)


@main_bp.route('/dashboard_administrator')
def dashboard_administrator():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    if session.get('user_type') != 'System Administrator':
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('main.login'))
    return render_template('administrator_view.html')


# View all Panchayat Employees
@main_bp.route('/panchayat_employees')
def panchayat_employees():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    # Custom sorting to display Sarpanch first, Naib Sarpanch second, and others afterwards
    employees = db.session.execute(
        text("""
            SELECT * FROM Panchayat_Users
            ORDER BY 
                CASE 
                    WHEN designation = 'Sarpanch' THEN 1
                    WHEN designation = 'Naib Sarpanch' THEN 2
                    ELSE 3
                END,
                designation
        """)
    ).fetchall()

    return render_template('panchayat_employees.html', employees=employees)

# Add/Edit a Panchayat Employee
@main_bp.route('/add_edit_panchayat_employee/', defaults={'username': None}, methods=['GET', 'POST'])
@main_bp.route('/add_edit_panchayat_employee/<username>', methods=['GET', 'POST'])
def add_edit_panchayat_employee(username=None):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    form_username = ""
    form_password = ""
    form_designation = ""
    form_aadhar_no = ""
    old_password = ""
    errors = {
        'username': None,
        'password': None,
        'designation': None,
        'aadhar_no': None,
        'general': None
    }

    if request.method == 'GET' and username:
        # Fetch existing employee details for editing
        employee_result = db.session.execute(
            text("""
                SELECT username, password, designation, aadhar_no 
                FROM Panchayat_Users 
                WHERE username = :username
            """), 
            {'username': username}
        ).fetchone()

        if employee_result:
            form_username, old_password, form_designation, form_aadhar_no = employee_result
            form_password = ""

    if request.method == 'POST':
        form_username = request.form.get('username', '').strip()
        form_password = request.form.get('password', '').strip()
        form_designation = request.form.get('designation', '').strip()

        # Aadhar number remains unchanged during edit
        if not username:  # Only set aadhar number during addition
            form_aadhar_no = request.form.get('aadhar_no', '').strip()
        else:
            # Retrieve the existing aadhar number for the edit case
            employee_result = db.session.execute(
                text("SELECT aadhar_no FROM Panchayat_Users WHERE username = :username"),
                {'username': username}
            ).fetchone()
            form_aadhar_no = employee_result[0] if employee_result else ""

        # Validation checks
        is_valid = True
        if not form_username:
            errors['username'] = 'Username is required'
            is_valid = False
        
        if not form_designation:
            errors['designation'] = 'Designation is required'
            is_valid = False
            
        if not username and not form_password:  # Password is mandatory when adding a new user
            errors['password'] = 'Password is required for new employees'
            is_valid = False
            
        if not username and not form_aadhar_no:
            errors['aadhar_no'] = 'Aadhar number is required'
            is_valid = False

        if is_valid:
            try:
                if username:  # Editing existing employee
                    # Fetch old password to retain if new password is blank or has only spaces
                    employee_result = db.session.execute(
                        text("SELECT password FROM Panchayat_Users WHERE username = :username"),
                        {'username': username}
                    ).fetchone()
                    
                    old_password = employee_result[0] if employee_result else ""

                    # Use old password if new password is blank or contains only spaces
                    update_password = old_password
                    if form_password:
                        # Encrypt the new password
                        from hashlib import md5
                        update_password = md5(form_password.encode()).hexdigest()

                    db.session.execute(
                        text("""
                            UPDATE Panchayat_Users 
                            SET username = :username, 
                                password = :password, 
                                designation = :designation
                            WHERE username = :old_username
                        """), 
                        {
                            'username': form_username,
                            'password': update_password,
                            'designation': form_designation,
                            'old_username': username
                        }
                    )
                    db.session.commit()
                    return redirect(url_for('main.panchayat_employees'))
                else:  # Adding a new employee
                    # Check if username already exists
                    existing_user = db.session.execute(
                        text("SELECT username FROM Panchayat_Users WHERE username = :username"),
                        {'username': form_username}
                    ).fetchone()
                    
                    if existing_user:
                        errors['username'] = 'Username already taken. Choose another.'
                    else:
                        # Check if aadhar number already exists
                        existing_aadhar = db.session.execute(
                            text("SELECT aadhar_no FROM Panchayat_Users WHERE aadhar_no = :aadhar_no"),
                            {'aadhar_no': form_aadhar_no}
                        ).fetchone()
                        
                        if existing_aadhar:
                            errors['aadhar_no'] = 'Aadhar number already in use.'
                        else:
                            # Encrypt the password
                            from hashlib import md5
                            encrypted_password = md5(form_password.encode()).hexdigest()
                            
                            db.session.execute(
                                text("""
                                    INSERT INTO Panchayat_Users (username, password, designation, aadhar_no)
                                    VALUES (:username, :password, :designation, :aadhar_no)
                                """), 
                                {
                                    'username': form_username,
                                    'password': encrypted_password,
                                    'designation': form_designation,
                                    'aadhar_no': form_aadhar_no
                                }
                            )
                            db.session.commit()
                            return redirect(url_for('main.panchayat_employees'))
            
            except Exception as e:
                db.session.rollback()
                # Check if it's an integrity error
                if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e) or "integrity constraint violation" in str(e):
                    if "username" in str(e):
                        errors['username'] = 'Username already exists. Please choose a different one.'
                    elif "aadhar_no" in str(e):
                        errors['aadhar_no'] = 'Aadhar number already associated with another employee.'
                    else:
                        errors['general'] = 'Database error occurred.'
                else:
                    errors['general'] = 'An unexpected error occurred.'

    # Prepare form data for rendering
    form_data = {
        'username': form_username,
        'password': form_password,
        'designation': form_designation,
        'aadhar_no': form_aadhar_no
    }

    # Render the template with the current form values and errors
    return render_template('panchayat_employees_form.html', 
                          form_data=form_data, 
                          errors=errors, 
                          is_edit=bool(username))


# Delete a Panchayat Employee
@main_bp.route('/delete_panchayat_employee/<username>', methods=['POST'])
def delete_panchayat_employee(username):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    try:
        employee = PanchayatUsers.query.filter_by(username=username).first()
        if employee:
            db.session.delete(employee)
            db.session.commit()
        else:
            flash('Employee not found!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {str(e)}', 'danger')

    return redirect(url_for('main.panchayat_employees'))

# View all Government Officials
@main_bp.route('/government_officials', methods=['GET'])
def government_officials():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    officials = SystemUsersTop.query.filter_by(user_type='Government Official').all()
    return render_template('government_officials.html', officials=officials)

# Add Edit all Government Officials
@main_bp.route('/add_edit_government_official/', defaults={'username': None}, methods=['GET', 'POST'])
@main_bp.route('/add_edit_government_official/<username>', methods=['GET', 'POST'])
def add_edit_government_official(username=None):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    form = GovernmentOfficialForm()
    official = None

    if username:
        official = SystemUsersTop.query.filter_by(username=username).first()
        if official:
            form.username.data = official.username  # Prefill username
            form.password.data = ""  # Keep password field blank for security

    if request.method == 'POST':
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()
        
        form.username.data = username_input
        form.password.data = password_input

        is_valid = True
        
        if not username_input:
            form.username.errors = ["Username is required!"]
            is_valid = False

        if not official and not password_input:  # New official requires password
            form.password.errors = ["Password is required for new officials!"]
            is_valid = False

        if is_valid:
            try:
                if official:  # Editing existing official
                    if password_input:  # User entered a new password
                        # Use MD5 which produces a 32-character hash - less secure but fits in the field
                        from hashlib import md5
                        hashed_password = md5(password_input.encode()).hexdigest()
                        official.password = hashed_password

                    official.username = username_input  # Update username
                    db.session.commit()
                    return redirect(url_for('main.government_officials'))

                else:  # Adding a new official
                    # Ensure the username is unique
                    existing_user = SystemUsersTop.query.filter_by(username=username_input).first()
                    if existing_user:
                        form.username.errors = ["Username already exists! Choose a different one."]
                    else:
                        # Use MD5 which produces a 32-character hash
                        from hashlib import md5
                        hashed_password = md5(password_input.encode()).hexdigest()
                        
                        # Create a new official with encrypted password
                        new_official = SystemUsersTop(
                            username=username_input,
                            password=hashed_password,
                            user_type='Government Official'
                        )
                        db.session.add(new_official)
                        db.session.commit()
                        return redirect(url_for('main.government_officials'))
            
            except Exception as e:
                db.session.rollback()
                # Print the error for debugging
                print(f"Database error: {str(e)}")
                if "UNIQUE constraint failed" in str(e) or "Duplicate entry" in str(e):
                    form.username.errors = ["Username already exists! Choose a different one."]
                else:
                    flash(f"An error occurred: {str(e)}", "danger")

    return render_template('government_officials_form.html', form=form, username=username)

# Delete a Government Official
@main_bp.route('/delete_government_official/<username>', methods=['POST'])
def delete_government_official(username):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    official = SystemUsersTop.query.filter_by(username=username).first()
    if official:
        db.session.delete(official)
        db.session.commit()

    return redirect(url_for('main.government_officials'))

# View the details of the citizen
@main_bp.route('/citizen/<aadhar_no>')
def citizen(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    # Query citizen's house_no directly
    house_no_result = db.session.execute(
        text("""
            SELECT House_No FROM Citizens 
            WHERE Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchone()
    
    if not house_no_result:
        flash('Citizen record not found.', 'danger')
        return redirect(url_for('main.dashboard_administrator'))
    
    house_no = house_no_result[0]
    
    # Now query all citizen information
    citizen_result = db.session.execute(
        text("""
            SELECT * FROM Citizens 
            WHERE Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchone()
    
    # Query household information
    household = db.session.execute(
        text("""
            SELECT * FROM Household 
            WHERE House_No = :house_no
        """), 
        {'house_no': house_no}
    ).fetchone()
    
    # Query health check-up data
    health_data = db.session.execute(
        text("""
            SELECT CheckUp_ID, Medical_Condition, Prescription, Date_of_Visit 
            FROM Health_CheckUp 
            WHERE Aadhar_No = :aadhar_no 
            ORDER BY Date_of_Visit DESC
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchall()
    
    # Query tax information
    tax_data = db.session.execute(
        text("""
            SELECT Tax_Amount, Payment_Status 
            FROM Taxation 
            WHERE Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchone()
    
    # Query welfare schemes
    welfare_data = db.session.execute(
        text("""
            SELECT ws.Scheme_Type, ws.Scheme_Description, a.Avail_Date
            FROM Welfare_Schemes ws
            JOIN Avails a ON ws.Scheme_ID = a.Scheme_ID
            WHERE a.Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchall()
    
    # Query agricultural land data
    agriculture_data = db.session.execute(
        text("""
            SELECT Land_ID, Area_in_Acres, Crop_Type, Soil_Type
            FROM Agricultural_Land
            WHERE Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchall()
    
    # Query resources data
    resources_data = db.session.execute(
        text("""
            SELECT Resource_ID, Resource_Name, Last_Inspected_Date
            FROM Resources
        """)
    ).fetchall()
    
    # Query complaints data
    complaints_data = db.session.execute(
        text("""
            SELECT c.Complaint_ID, r.Resource_Name, c.Complaint_Desc, c.Complain_Date
            FROM Complaints c
            JOIN Resources r ON c.Resource_ID = r.Resource_ID
            WHERE c.Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchall()
    
    # Query government institutions by type
    education_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Educational'
        """)
    ).fetchall()
    
    # Query health institutions by type
    health_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Health'
        """)
    ).fetchall()
    
    # Query banking institutions by type
    banking_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Banking'
        """)
    ).fetchall()
    
    # Query administrative institutions by type
    admin_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Administration'
        """)
    ).fetchall()
    
    # Get certificates
    certificates = db.session.execute(
        text("""
            SELECT Certificate_ID, Certificate_Type, Date_of_Issue
            FROM Certificates
            WHERE Aadhar_No = :aadhar_no
        """), 
        {'aadhar_no': aadhar_no}
    ).fetchall()
    
    return render_template(
        'citizen.html',
        citizen=citizen_result,
        household=household,
        health_data=health_data,
        tax_data=tax_data,
        welfare_data=welfare_data,
        agriculture_data=agriculture_data,
        resources_data=resources_data,
        complaints_data=complaints_data,
        education_institutions=education_institutions,
        health_institutions=health_institutions,
        banking_institutions=banking_institutions,
        admin_institutions=admin_institutions,
        certificates=certificates
    )


# Government official Dashboard
@main_bp.route('/dashboard_official', methods=['GET'])
def dashboard_official():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard_official.html')

# Census Dashboard in government official
@main_bp.route('/census', methods=['GET'])
def census():
    # Total people alive now
    total_alive = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Is_Alive = TRUE")).scalar()

    # Total male
    total_male = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Gender = 'Male' AND Is_Alive = TRUE")).scalar()

    # Total female
    total_female = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Gender = 'Female' AND Is_Alive = TRUE")).scalar()

    # Employment status bar
    employment_data = db.session.execute(text("""
        SELECT Employment, COUNT(*) 
        FROM Citizens 
        WHERE Is_Alive = TRUE
        GROUP BY Employment
    """)).fetchall()

    # Age distribution data
    below_18 = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM Citizens 
        WHERE DATE_PART('year', AGE(DOB)) < 18 AND Is_Alive = TRUE
    """)).scalar()
    age_18_to_60 = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM Citizens 
        WHERE DATE_PART('year', AGE(DOB)) BETWEEN 18 AND 60 AND Is_Alive = TRUE
    """)).scalar()
    above_60 = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM Citizens 
        WHERE DATE_PART('year', AGE(DOB)) > 60 AND Is_Alive = TRUE
    """)).scalar()

    # Education level bar
    education_data = db.session.execute(text("""
        SELECT Education_Level, COUNT(*) 
        FROM Citizens 
        WHERE Is_Alive = TRUE
        GROUP BY Education_Level
    """)).fetchall()

    # Deaths this year
    deaths_this_year = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM Certificates 
        WHERE Certificate_Type = 'Death' AND EXTRACT(YEAR FROM Date_of_Issue) = EXTRACT(YEAR FROM CURRENT_DATE)
    """)).scalar()

    # Births this year
    births_this_year = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM Certificates 
        WHERE Certificate_Type = 'Birth' AND EXTRACT(YEAR FROM Date_of_Issue) = EXTRACT(YEAR FROM CURRENT_DATE)
    """)).scalar()

    return render_template(
        'census.html',
        total_alive=total_alive,
        total_male=total_male,
        total_female=total_female,
        employment_data=employment_data,
        below_18=below_18,
        age_18_to_60=age_18_to_60,
        above_60=above_60,
        education_data=education_data,
        deaths_this_year=deaths_this_year,
        births_this_year=births_this_year,
    )

# Taxation Dashboard in government official
@main_bp.route('/taxation', methods=['GET'])
def taxation():
    # Total people who have not paid tax
    not_paid_tax_count = db.session.execute(text("SELECT COUNT(*) FROM Taxation WHERE Payment_Status = FALSE")).scalar()

    # List of people who have not paid tax (with contact number and address)
    people_not_paid_tax = db.session.execute(text("""
        SELECT c.Name, c.Phone_No, h.Address 
        FROM Citizens c 
        JOIN Household h ON c.House_No = h.House_No 
        JOIN Taxation t ON c.Aadhar_No = t.Aadhar_No 
        WHERE t.Payment_Status = FALSE
    """)).fetchall()

    # Total amount of tax paid / total amount of tax owed
    tax_summary = db.session.execute(text("""
        SELECT SUM(CASE WHEN Payment_Status THEN Tax_Amount ELSE 0 END) AS paid_tax,
               SUM(Tax_Amount) AS total_tax 
        FROM Taxation
    """)).fetchone()

    return render_template(
        'taxation.html',
        not_paid_tax_count=not_paid_tax_count,
        people_not_paid_tax=people_not_paid_tax,
        tax_summary=tax_summary,
    )

# Health Dashboard in government official
@main_bp.route('/health', methods=['GET'])
def health():
    # Disease-specific count bar for this year
    disease_data = db.session.execute(text("""
        SELECT Medical_Condition, COUNT(*) 
        FROM Health_CheckUp 
        WHERE EXTRACT(YEAR FROM Date_of_Visit) = EXTRACT(YEAR FROM CURRENT_DATE)
        GROUP BY Medical_Condition
    """)).fetchall()

    return render_template('health.html', disease_data=disease_data)

@main_bp.route('/welfare_schemes', methods=['GET'])
def welfare_schemes():
    # Fetch all welfare schemes
    schemes = db.session.execute(text("SELECT * FROM Welfare_Schemes")).fetchall()
    
    # Fetch the total budget
    total_budget = db.session.execute(text("SELECT SUM(budget) FROM Welfare_Schemes")).scalar() or 0

    return render_template('welfare_schemes.html', schemes=schemes, total_budget=total_budget)

@main_bp.route('/agriculture_data', methods=['GET'])
def agriculture_data():
    # Total land area under cultivation
    total_land_area = db.session.execute(text("SELECT SUM(Area_in_Acres) FROM Agricultural_Land")).scalar() or 0

    # Crop name - land area chart data
    crop_data = db.session.execute(text("""
        SELECT Crop_Type, SUM(Area_in_Acres) 
        FROM Agricultural_Land 
        GROUP BY Crop_Type
    """)).fetchall()

    return render_template(
        'agriculture_data.html',
        total_land_area=total_land_area,
        crop_data=crop_data,
    )

@main_bp.route('/institutions', methods=['GET'])
def institutions():
    # Get counts by institution type
    institution_counts = db.session.execute(text("""
       SELECT Institute_Type, COUNT(*)
       FROM Government_Institutions 
       GROUP BY Institute_Type;
    """)).fetchall()
    
    # Get detailed institution data
    institutions_by_type = {}
    for inst_type, _ in institution_counts:
        institutions_by_type[inst_type] = db.session.execute(text("""
            SELECT * FROM Government_Institutions 
            WHERE Institute_Type = :type
        """), {"type": inst_type}).fetchall()
    
    return render_template(
        'institutions.html', 
        institution_counts=institution_counts,
        institutions_by_type=institutions_by_type
    )

# Panchayat Employees Dashboard
@main_bp.route('/dashboard_employees', methods=['GET'])
def dashboard_employees():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard_employees.html')

# Add/ View/ Modify/ Delete Citizens
@main_bp.route('/manage_citizens', methods=['GET'])
def manage_citizens():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizens_list = Citizens.query.filter_by(is_alive=True).all()
    return render_template('manage_citizens.html', citizens=citizens_list)

# Add citizens
@main_bp.route('/add_citizen', methods=['GET', 'POST'])
def add_citizen():
    form_data = request.form.to_dict() if request.method == 'POST' else {}
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        name = request.form.get('name', '').strip()
        dob_str = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        house_no = request.form.get('house_no', '').strip()
        phone_no = request.form.get('phone_no', '').strip()
        email_id = request.form.get('email_id', '').strip()
        education_level = request.form.get('education_level', 'Uneducated').strip()
        income_str = request.form.get('income', '0').strip()
        employment = request.form.get('employment', 'Unemployed').strip()
        is_alive = True

        # Validate all required fields
        if not all([aadhar_no, name, dob_str, gender, house_no, education_level, income_str, employment]):
            flash("All required fields must be filled!", "danger")
            return render_template('add_citizen.html', form_data=form_data)

        # Validate Aadhar Number (12 digits)
        if len(aadhar_no) != 12 or not aadhar_no.isdigit():
            flash("Aadhar number must be exactly 12 digits!", "aadhar_no_error")
            return render_template('add_citizen.html', form_data=form_data)

        # Check if Citizen Already Exists
        existing_citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if existing_citizen:
            flash("Citizen with this Aadhar number already exists!", "aadhar_no_error")
            return render_template('add_citizen.html', form_data=form_data)

        # Validate Date of Birth (YYYY-MM-DD format)
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format! Use YYYY-MM-DD.", "danger")
            return render_template('add_citizen.html', form_data=form_data)

        # Convert House Number to Integer
        if not house_no.isdigit():
            flash("House number must be a number!", "house_no_error")
            return render_template('add_citizen.html', form_data=form_data)
        house_no = int(house_no)

        # Check if Household Number exists
        household = db.session.query(Household).filter_by(house_no=house_no).first()
        if not household:
            flash("Household number does not exist!", "house_no_error")
            return render_template('add_citizen.html', form_data=form_data)
        
        # Check if email is '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if email_id and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_id):
            flash("Invalid email address!", "email_id_error")
            return render_template('add_citizen.html', form_data=form_data)        

        # Convert Income to Numeric
        try:
            income = int(income_str)
        except ValueError:
            flash("Income must be a valid number!", "danger")
            return render_template('add_citizen.html', form_data=form_data)

        # Validate Phone Number
        if phone_no and (not phone_no.isdigit() or len(phone_no) != 10 or phone_no[0] not in '6789'):
            flash("Invalid phone number! It must contain only numbers, be exactly 10 digits, and start with 6 to 9.", "phone_no_error")
            return render_template('add_citizen.html', form_data=form_data)

        # Create New Citizen Entry
        new_citizen = Citizens(
            aadhar_no=aadhar_no,
            name=name,
            dob=dob,
            gender=gender,
            house_no=house_no,
            phone_no=phone_no,
            email_id=email_id,
            education_level=education_level,
            income=income,
            employment=employment,
            is_alive=is_alive
        )

        db.session.add(new_citizen)
        db.session.flush()  # Ensures record is created before committing

        # Automatically Create Birth Certificate
        new_certificate = Certificates(
            aadhar_no=aadhar_no,
            certificate_type='Birth',
            date_of_issue=dob
        )
        db.session.add(new_certificate)

        # Check Income for Taxation
        if income >= 10000:
            tax_amount = income * 0.18  # Calculate 18% tax
            new_taxation = Taxation(
                aadhar_no=aadhar_no,
                tax_amount=int(tax_amount),
                payment_status=False  # Default payment status is false
            )
            db.session.add(new_taxation)

        # Commit Changes
        try:
            db.session.commit()
            return redirect(url_for('main.manage_citizens'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding citizen: {str(e)}", "danger")
            return render_template('add_citizen.html', form_data=form_data)

    return render_template('add_citizen.html', form_data=form_data)

@main_bp.route('/delete_citizen', methods=['GET', 'POST'])
def delete_citizen():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        # If aadhar_no is provided, find the citizen
        if aadhar_no:
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            if not citizen:
                flash("Citizen not found with this Aadhar number!", "danger")
                return redirect(url_for('main.delete_citizen'))
    
    # If aadhar_no is provided in the URL (for direct access)
    if request.args.get('aadhar_no'):
        aadhar_no = request.args.get('aadhar_no')
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen not found with this Aadhar number!", "danger")
            return redirect(url_for('main.delete_citizen'))
    
    return render_template('delete_citizen.html', citizen=citizen)

# Confirm deletion of citizen
@main_bp.route('/delete_citizen_confirm/<aadhar_no>', methods=['POST'])
def delete_citizen_confirm(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen not found!", "danger")
            return redirect(url_for('main.manage_citizens'))
        
        # Delete all related records
        
        # Delete certificates
        Certificates.query.filter_by(aadhar_no=aadhar_no).delete()
        
        # Delete taxation records
        Taxation.query.filter_by(aadhar_no=aadhar_no).delete()
        
        # Delete health records
        Health_CheckUp.query.filter_by(aadhar_no=aadhar_no).delete()
        
        # Delete complaints
        Complaints.query.filter_by(aadhar_no=aadhar_no).delete()
        
        PanchayatUsers.query.filter_by(aadhar_no=aadhar_no).delete()
        
        # Delete welfare scheme enrollments
        db.session.execute(
            text("DELETE FROM Avails WHERE Aadhar_No = :aadhar_no"),
            {'aadhar_no': aadhar_no}
        )
        
        # Delete agricultural land records
        Agricultural_Land.query.filter_by(aadhar_no=aadhar_no).delete()
        
        # Finally delete the citizen
        db.session.delete(citizen)
        db.session.commit()
        
        return redirect(url_for('main.manage_citizens'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting citizen: {str(e)}", "danger")
        return redirect(url_for('main.delete_citizen'))

# Modify Citizen Data
@main_bp.route('/modify_citizen', methods=['GET', 'POST'])
def modify_citizen():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        # If aadhar_no is provided, find the citizen
        if aadhar_no:
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            if not citizen:
                flash("Citizen not found with this Aadhar number!", "danger")
                return redirect(url_for('main.modify_citizen'))
    
    # If aadhar_no is provided in the URL (for direct access)
    if request.args.get('aadhar_no'):
        aadhar_no = request.args.get('aadhar_no')
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen not found with this Aadhar number!", "danger")
            return redirect(url_for('main.modify_citizen'))
    
    return render_template('modify_citizen.html', citizen=citizen)

# Modify the citizens data using aadhar no
@main_bp.route('/modify_citizen_submit/<aadhar_no>', methods=['POST'])
def modify_citizen_submit(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen not found!", "danger")
            return redirect(url_for('main.manage_citizens'))
        
        # Get the new income value
        new_income_str = request.form.get('income', '0').strip()
        new_income = int(new_income_str) if new_income_str else 0
        old_income = int(citizen.income) if citizen.income else 0
        
        # Update citizen information
        citizen.name = request.form.get('name', '').strip()
        citizen.dob = request.form.get('dob', '').strip()
        citizen.gender = request.form.get('gender', '').strip()
        citizen.house_no = request.form.get('house_no', '').strip()
        citizen.phone_no = request.form.get('phone_no', '').strip()
        citizen.email_id = request.form.get('email_id', '').strip()
        citizen.education_level = request.form.get('education_level', '').strip()
        citizen.income = new_income
        citizen.employment = request.form.get('employment', '').strip()
        citizen.is_alive = citizen.is_alive  # Keep the same   
        
        # If income has changed, update the taxation record
        if new_income != old_income:
            # Calculate new tax amount (18% of income) as integer
            new_tax_amount = int(new_income * 0.18)
            
            # Update the taxation record
            taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
            
            if taxation_record:
                # Update existing taxation record
                taxation_record.tax_amount = new_tax_amount
                # Reset payment status to False since income changed
                taxation_record.payment_status = False
            else:
                # Create new taxation record if it doesn't exist
                new_taxation = Taxation(
                    aadhar_no=aadhar_no,
                    tax_amount=new_tax_amount,
                    payment_status=False
                )
                db.session.add(new_taxation)
        
        db.session.commit()
        
        return redirect(url_for('main.manage_citizens'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating citizen: {str(e)}", "danger")
        return redirect(url_for('main.modify_citizen', aadhar_no=aadhar_no))

# Add/ View/ Delete/ Modify Certificates
@main_bp.route('/manage_certificates', methods=['GET'])
def manage_certificates():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_certificates.html')

# Add certificates
@main_bp.route('/add_certificate', methods=['GET', 'POST'])
def add_certificate():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    error_message = None
    prefilled_aadhar = request.args.get('aadhar_no', '')
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        certificate_type = request.form.get('certificate_type', '').strip()
        date_of_issue = request.form.get('date_of_issue', '').strip()
        
        # Validate inputs
        if not all([aadhar_no, certificate_type, date_of_issue]):
            error_message = "All fields are required!"
            return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        
        if not citizen:
            error_message = "Citizen with this Aadhar number does not exist!"
            return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)
        
        # Check for duplicate birth certificate
        if certificate_type == 'Birth':
            existing_birth = Certificates.query.filter_by(
                aadhar_no=aadhar_no, 
                certificate_type='Birth'
            ).first()
            
            if existing_birth:
                error_message = "Birth certificate already exists for this citizen!"
                return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)
            
            # Validate birth certificate date matches DOB
            if date_of_issue != citizen.dob.strftime('%Y-%m-%d'):
                error_message = "For birth certificates, the date of issue must be the same as the citizen's date of birth!"
                return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)

        
        # Check for duplicate death certificate
        if certificate_type == 'Death':
            existing_death = Certificates.query.filter_by(
                aadhar_no=aadhar_no, 
                certificate_type='Death'
            ).first()
            
            if existing_death:
                error_message = "Death certificate already exists for this citizen!"
                return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)
            
            # Update citizen status to deceased
            if citizen.is_alive:
                citizen.is_alive = False
        
        try:
            # Create new certificate
            new_certificate = Certificates(
                aadhar_no=aadhar_no,
                certificate_type=certificate_type,
                date_of_issue=date_of_issue
            )
            
            db.session.add(new_certificate)
            db.session.commit()
            return redirect(url_for('main.find_certificates'))
        except Exception as e:
            db.session.rollback()
            error_message = f"Error adding certificate: {str(e)}"
            return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=aadhar_no)
    
    return render_template('add_certificate.html', error_message=error_message, prefilled_aadhar=prefilled_aadhar)

@main_bp.route('/find_certificates', methods=['GET', 'POST'])
def find_certificates():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    certificates = None
    error_message = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        if not aadhar_no:
            error_message = "Aadhar number is required!"
        else:
            # Find citizen
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            
            if not citizen:
                error_message = "Citizen with this Aadhar number does not exist!"
            else:
                # Get certificates for this citizen
                certificates = Certificates.query.filter_by(aadhar_no=aadhar_no).all()
    
    return render_template('find_certificates.html', 
                          citizen=citizen, 
                          certificates=certificates, 
                          error_message=error_message)

# Modify Certificates
@main_bp.route('/modify_certificate/<int:certificate_id>', methods=['GET'])
def modify_certificate(certificate_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    certificate = Certificates.query.get(certificate_id)
    if not certificate:
        flash("Certificate not found!", "danger")
        return redirect(url_for('main.manage_certificates'))
    
    citizen = Citizens.query.filter_by(aadhar_no=certificate.aadhar_no).first()
    
    return render_template('modify_certificate.html', certificate=certificate, citizen=citizen)

# Modify Certificates Submit
@main_bp.route('/modify_certificate_submit/<certificate_id>', methods=['POST'])
def modify_certificate_submit(certificate_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    certificate = Certificates.query.get(certificate_id)
    if not certificate:
        flash("Certificate not found!", "danger")
        return redirect(url_for('main.manage_certificates'))
    
    try:
        certificate_type = request.form.get('certificate_type', '').strip()
        date_of_issue = request.form.get('date_of_issue', '').strip()
        
        if not all([certificate_type, date_of_issue]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.modify_certificate', certificate_id=certificate_id))
        
        # Get citizen for DOB validation
        citizen = Citizens.query.filter_by(aadhar_no=certificate.aadhar_no).first()
        
        # Validate birth certificate date matches DOB
        if certificate_type == 'Birth':
            if date_of_issue != citizen.dob.strftime('%Y-%m-%d'):
                flash("For birth certificates, the date of issue must be the same as the citizen's date of birth!", "danger")
                return redirect(url_for('main.modify_certificate', certificate_id=certificate_id))

        # Update certificate
        certificate.certificate_type = certificate_type
        certificate.date_of_issue = date_of_issue
        
        # Special handling for Death certificates
        if certificate_type == 'Death':
            if citizen and citizen.is_alive:
                citizen.is_alive = False
        
        db.session.commit()
        return redirect(url_for('main.find_certificates'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating certificate: {str(e)}", "danger")
        return redirect(url_for('main.modify_certificate', certificate_id=certificate_id))

# Delete Certificate
@main_bp.route('/delete_certificate/<int:certificate_id>', methods=['GET'])
def delete_certificate(certificate_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    certificate = Certificates.query.get(certificate_id)
    if not certificate:
        flash("Certificate not found!", "danger")
        return redirect(url_for('main.manage_certificates'))
    
    citizen = Citizens.query.filter_by(aadhar_no=certificate.aadhar_no).first()
    
    return render_template('delete_certificate.html', certificate=certificate, citizen=citizen)

# Delete Certificate Confirm
@main_bp.route('/delete_certificate_confirm/<int:certificate_id>', methods=['POST'])
def delete_certificate_confirm(certificate_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        certificate = Certificates.query.get(certificate_id)
        if not certificate:
            flash("Certificate not found!", "danger")
            return redirect(url_for('main.manage_certificates'))
                
        # Delete the certificate
        db.session.delete(certificate)
        db.session.commit()
                
        # Redirect back to find certificates with the same Aadhar number
        return redirect(url_for('main.find_certificates'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting certificate: {str(e)}", "danger")
        return redirect(url_for('main.delete_certificate', certificate_id=certificate_id))

# Add/ View/ Delete/ Modify Welfare Schemes
@main_bp.route('/manage_welfare_schemes', methods=['GET', 'POST'])
def manage_welfare_schemes():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            # Delete welfare scheme logic
            scheme_id = request.form.get('scheme_id')
            scheme = Welfare_Schemes.query.filter_by(scheme_id=scheme_id).first()
            
            if scheme:
                try:
                    # First delete any avails records that reference this scheme
                    db.session.execute(
                        text("DELETE FROM Avails WHERE Scheme_ID = :scheme_id"),
                        {'scheme_id': scheme_id}
                    )
                    
                    # Then delete the scheme
                    db.session.delete(scheme)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error deleting scheme: {str(e)}", "danger")
            else:
                flash("Welfare Scheme not found!", "danger")
    
    # Get all welfare schemes
    schemes_list = Welfare_Schemes.query.order_by(Welfare_Schemes.scheme_id).all()
    return render_template('manage_welfare_schemes.html', schemes=schemes_list)

# Add Welfare Scheme
@main_bp.route('/add_welfare_scheme', methods=['GET', 'POST'])
def add_welfare_scheme():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        scheme_type = request.form.get('scheme_type', '').strip()
        budget = request.form.get('budget', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate inputs
        if not all([scheme_type, budget, description]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.add_welfare_scheme'))
        
        # Check for duplicate scheme description (case-insensitive)
        existing_scheme = db.session.execute(
            text("SELECT * FROM Welfare_Schemes WHERE LOWER(scheme_description) = LOWER(:description)"),
            {"description": description}
        ).fetchone()
        
        if existing_scheme:
            flash("A welfare scheme with this description already exists!", "danger")
            return render_template('add_welfare_scheme.html', 
                                  scheme_type=scheme_type, 
                                  budget=budget, 
                                  description=description)
        
        try:
            # Create new welfare scheme
            new_scheme = Welfare_Schemes(
                scheme_type=scheme_type,
                budget=budget,
                scheme_description=description
            )
            
            db.session.add(new_scheme)
            db.session.commit()
            return redirect(url_for('main.manage_welfare_schemes'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding welfare scheme: {str(e)}", "danger")
            return redirect(url_for('main.add_welfare_scheme'))
    
    return render_template('add_welfare_scheme.html')

# Modify welfare scheme
@main_bp.route('/modify_welfare_scheme/<int:scheme_id>', methods=['GET'])
def modify_welfare_scheme(scheme_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    scheme = Welfare_Schemes.query.get(scheme_id)
    if not scheme:
        flash("Welfare Scheme not found!", "danger")
        return redirect(url_for('main.manage_welfare_schemes'))
    
    return render_template('modify_welfare_scheme.html', scheme=scheme)

# Modify welfare scheme submit
@main_bp.route('/modify_welfare_scheme_submit/<scheme_id>', methods=['POST'])
def modify_welfare_scheme_submit(scheme_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    scheme = Welfare_Schemes.query.get(scheme_id)
    if not scheme:
        flash("Welfare Scheme not found!", "danger")
        return redirect(url_for('main.manage_welfare_schemes'))
    
    try:
        scheme_type = request.form.get('scheme_type', '').strip()
        budget = request.form.get('budget', '').strip()
        description = request.form.get('description', '').strip()
        
        if not all([scheme_type, budget, description]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.modify_welfare_scheme', scheme_id=scheme_id))
        
        # Check for duplicate scheme description (case-insensitive), excluding current scheme
        existing_scheme = db.session.execute(
            text("""
                SELECT * FROM Welfare_Schemes 
                WHERE LOWER(scheme_description) = LOWER(:description) 
                AND scheme_id != :scheme_id
            """),
            {"description": description, "scheme_id": scheme_id}
        ).fetchone()
        
        if existing_scheme:
            flash("A welfare scheme with this description already exists!", "danger")
            return redirect(url_for('main.modify_welfare_scheme', scheme_id=scheme_id))
        
        # Update scheme
        scheme.scheme_type = scheme_type
        scheme.budget = budget
        scheme.scheme_description = description
        
        db.session.commit()
        return redirect(url_for('main.manage_welfare_schemes'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating welfare scheme: {str(e)}", "danger")
        return redirect(url_for('main.modify_welfare_scheme', scheme_id=scheme_id))

# Add/ View/ Delete/ Modify agricultural land
@main_bp.route('/manage_agriculture_land', methods=['GET', 'POST'])
def manage_agriculture_land():
    if 'user' not in session:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete':
            # Delete agriculture land logic
            land_id = request.form.get('land_id')
            land = Agricultural_Land.query.filter_by(land_id=land_id).first()
            
            if land:
                try:
                    db.session.delete(land)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error deleting land record: {str(e)}", "danger")
            else:
                flash("Agricultural land record not found!", "danger")
    
    # Join with Citizens table to get owner names
    lands_data = db.session.execute(
        text("""
        SELECT al.Land_ID, al.Aadhar_No, c.Name, al.Area_in_Acres, al.Crop_Type, al.Soil_Type
        FROM Agricultural_Land al
        JOIN Citizens c ON al.Aadhar_No = c.Aadhar_No
        ORDER BY al.Land_ID
        """)
    ).fetchall()
    
    # Convert to list of dictionaries for template
    lands_list = []
    for land in lands_data:
        lands_list.append({
            'land_id': land[0],
            'aadhar_no': land[1],
            'citizen_name': land[2],
            'area_in_acres': land[3],
            'crop_type': land[4],
            'soil_type': land[5]
        })
    
    return render_template('manage_agriculture_land.html', lands=lands_list)

# Add agricultural land
@main_bp.route('/add_agriculture_land', methods=['GET', 'POST'])
def add_agriculture_land():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        area_in_acres = request.form.get('area_in_acres', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        soil_type = request.form.get('soil_type', '').strip()
        
        # Validate inputs
        if not all([aadhar_no, area_in_acres, crop_type, soil_type]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.add_agriculture_land'))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.add_agriculture_land'))
        
        try:
            # Create new agricultural land record
            new_land = Agricultural_Land(
                aadhar_no=aadhar_no,
                area_in_acres=area_in_acres,
                crop_type=crop_type,
                soil_type=soil_type
            )
            
            db.session.add(new_land)
            db.session.commit()
            
            return redirect(url_for('main.manage_agriculture_land'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding agricultural land: {str(e)}", "danger")
            return redirect(url_for('main.add_agriculture_land'))
    
    return render_template('add_agriculture_land.html')

# Modify agricultural land
@main_bp.route('/modify_agriculture_land/<int:land_id>', methods=['GET'])
def modify_agriculture_land(land_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    land = Agricultural_Land.query.get(land_id)
    if not land:
        flash("Agricultural land record not found!", "danger")
        return redirect(url_for('main.manage_agriculture_land'))
    
    citizen = Citizens.query.filter_by(aadhar_no=land.aadhar_no).first()
    
    return render_template('modify_agriculture_land.html', land=land, citizen=citizen)

# Modify agricultural land submit
@main_bp.route('/modify_agriculture_land_submit/<int:land_id>', methods=['POST'])
def modify_agriculture_land_submit(land_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    land = Agricultural_Land.query.get(land_id)
    if not land:
        flash("Agricultural land record not found!", "danger")
        return redirect(url_for('main.manage_agriculture_land'))
    
    try:
        area_in_acres = request.form.get('area_in_acres', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        soil_type = request.form.get('soil_type', '').strip()
        
        if not all([area_in_acres, crop_type, soil_type]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.modify_agriculture_land', land_id=land_id))
        
        land.area_in_acres = area_in_acres
        land.crop_type = crop_type
        land.soil_type = soil_type
        
        db.session.commit()
        
        return redirect(url_for('main.manage_agriculture_land'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating agricultural land: {str(e)}", "danger")
        return redirect(url_for('main.modify_agriculture_land', land_id=land_id))

# Add/ View/ Delete/ Modify Health Checkup Records
@main_bp.route('/manage_health_data', methods=['GET'])
def manage_health_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_health_data.html')

# Add Health Checkup Record
@main_bp.route('/add_health_data', methods=['GET', 'POST'])
def add_health_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    error_message = None
    form_data = {}
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        medical_condition = request.form.get('medical_condition', '').strip()
        prescription = request.form.get('prescription', '').strip()
        date_of_visit = request.form.get('date_of_visit', '').strip()
        
        form_data = {
            'aadhar_no': aadhar_no,
            'medical_condition': medical_condition,
            'prescription': prescription,
            'date_of_visit': date_of_visit
        }
        
        # Validate inputs
        if not all([aadhar_no, medical_condition, prescription, date_of_visit]):
            error_message = "All fields are required!"
            return render_template('add_health_data.html', error_message=error_message, form_data=form_data)
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            error_message = "Citizen with this Aadhar number does not exist!"
            return render_template('add_health_data.html', error_message=error_message, form_data=form_data, aadhar_error=True)
        
        try:
            # Create new health record
            new_record = Health_CheckUp(
                aadhar_no=aadhar_no,
                medical_condition=medical_condition,
                prescription=prescription,
                date_of_visit=date_of_visit
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            return redirect(url_for('main.manage_health_data'))
            
        except Exception as e:
            db.session.rollback()
            error_message = f"Error adding health record: {str(e)}"
            return render_template('add_health_data.html', error_message=error_message, form_data=form_data)
    
    return render_template('add_health_data.html', error_message=error_message, form_data=form_data)

# Find Health Records
@main_bp.route('/find_health_records', methods=['GET', 'POST'])
def find_health_records():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    health_records = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        if not aadhar_no:
            flash("Aadhar number is required!", "danger")
            return redirect(url_for('main.find_health_records'))
        
        # Find citizen
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.find_health_records'))
        
        # Get health records for this citizen
        health_records = Health_CheckUp.query.filter_by(aadhar_no=aadhar_no).order_by(Health_CheckUp.date_of_visit.desc()).all()
    
    return render_template('find_health_records.html', citizen=citizen, health_records=health_records)

# Modify Health Record
@main_bp.route('/modify_health_record/<int:checkup_id>', methods=['GET'])
def modify_health_record(checkup_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    record = Health_CheckUp.query.get(checkup_id)
    if not record:
        flash("Health record not found!", "danger")
        return redirect(url_for('main.manage_health_data'))
    
    citizen = Citizens.query.filter_by(aadhar_no=record.aadhar_no).first()
    
    return render_template('modify_health_record.html', record=record, citizen=citizen)

# Modify Health Record Submit
@main_bp.route('/modify_health_record_submit/<int:checkup_id>', methods=['POST'])
def modify_health_record_submit(checkup_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    record = Health_CheckUp.query.get(checkup_id)
    if not record:
        flash("Health record not found!", "danger")
        return redirect(url_for('main.manage_health_data'))
    
    try:
        medical_condition = request.form.get('medical_condition', '').strip()
        prescription = request.form.get('prescription', '').strip()
        date_of_visit = request.form.get('date_of_visit', '').strip()
        
        if not all([medical_condition, prescription, date_of_visit]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.modify_health_record', checkup_id=checkup_id))
        
        # Store the aadhar_no before updating the record
        aadhar_no = record.aadhar_no
        
        # Update record
        record.medical_condition = medical_condition
        record.prescription = prescription
        record.date_of_visit = date_of_visit
        
        db.session.commit()
                
        # Create a response with a form that auto-submits to find_health_records with the aadhar_no
        response = make_response("""
        <html>
        <body>
            <form id="redirectForm" method="POST" action="/find_health_records">
                <input type="hidden" name="aadhar_no" value="{}">
            </form>
            <script>
                document.getElementById('redirectForm').submit();
            </script>
        </body>
        </html>
        """.format(aadhar_no))
        
        return response
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating health record: {str(e)}", "danger")
        return redirect(url_for('main.modify_health_record', checkup_id=checkup_id))

# Delete Health Record
@main_bp.route('/delete_health_record', methods=['POST'])
def delete_health_record():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        checkup_id = request.form.get('checkup_id')
        record = Health_CheckUp.query.get(checkup_id)
        
        if not record:
            flash("Health record not found!", "danger")
            return redirect(url_for('main.manage_health_data'))
                
        db.session.delete(record)
        db.session.commit()
                
        # Redirect back to the same citizen's records
        return redirect(url_for('main.find_health_records'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting health record: {str(e)}", "danger")
        return redirect(url_for('main.find_health_records'))

# Add/ View/ Delete/ Modify Taxation Data
@main_bp.route('/manage_taxation_data', methods=['GET'])
def manage_taxation_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_taxation_data.html')

# Add Taxation Data
@main_bp.route('/add_taxation_data', methods=['GET', 'POST'])
def add_taxation_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    error_message = None
    prefilled_aadhar = request.args.get('aadhar_no', '')
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        tax_amount = request.form.get('tax_amount', '').strip()
        payment_status = False
        
        # Validate inputs
        if not all([aadhar_no, tax_amount]):
            error_message = "All fields are required!"
            return render_template('add_taxation_data.html', error_message=error_message, prefilled_aadhar=aadhar_no)
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            error_message = "Citizen with this Aadhar number does not exist!"
            return render_template('add_taxation_data.html', error_message=error_message, prefilled_aadhar=aadhar_no)
        
        # Check if taxation record already exists for this citizen
        existing_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
        if existing_record:
            error_message = "Taxation record already exists for this citizen!"
            return render_template('add_taxation_data.html', error_message=error_message, prefilled_aadhar=aadhar_no)
        
        try:
            # Create new taxation record
            new_record = Taxation(
                aadhar_no=aadhar_no,
                tax_amount=tax_amount,
                payment_status=payment_status
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            return redirect(url_for('main.manage_taxation_data'))
            
        except Exception as e:
            db.session.rollback()
            error_message = f"Error adding taxation record: {str(e)}"
            return render_template('add_taxation_data.html', error_message=error_message, prefilled_aadhar=aadhar_no)
    
    return render_template('add_taxation_data.html', error_message=error_message, prefilled_aadhar=prefilled_aadhar)

# Find Taxation Records
@main_bp.route('/find_taxation_records', methods=['GET', 'POST'])
def find_taxation_records():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    taxation_record = None
    error_message = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        if not aadhar_no:
            error_message = "Aadhar number is required!"
        else:
            # Find citizen
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            
            if not citizen:
                error_message = "Citizen with this Aadhar number does not exist!"
            else:
                # Get taxation record for this citizen
                taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
    
    return render_template('find_taxation_records.html', 
                          citizen=citizen, 
                          taxation_record=taxation_record, 
                          error_message=error_message)

# Modify Taxation Record
@main_bp.route('/modify_taxation_record/<string:aadhar_no>', methods=['GET'])
def modify_taxation_record(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
    if not taxation_record:
        flash("Taxation record not found!", "danger")
        return redirect(url_for('main.manage_taxation_data'))
    
    citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
    
    return render_template('modify_taxation_record.html', taxation_record=taxation_record, citizen=citizen)

# Modify Taxation Record Submit
@main_bp.route('/modify_taxation_record_submit/<string:aadhar_no>', methods=['POST'])
def modify_taxation_record_submit(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
    if not taxation_record:
        flash("Taxation record not found!", "danger")
        return redirect(url_for('main.manage_taxation_data'))
    
    try:
        tax_amount = request.form.get('tax_amount', '').strip()
        payment_status = 'payment_status' in request.form
        
        if not tax_amount:
            flash("Tax amount is required!", "danger")
            return redirect(url_for('main.modify_taxation_record', aadhar_no=aadhar_no))
        
        # Update record
        taxation_record.tax_amount = tax_amount
        taxation_record.payment_status = payment_status
        
        db.session.commit()
                
        # Redirect back to find_taxation_records with the aadhar_no as POST parameter
        response = make_response("""
        <html>
        <body>
            <form id="redirectForm" method="POST" action="/find_taxation_records">
                <input type="hidden" name="aadhar_no" value="{}">
            </form>
            <script>
                document.getElementById('redirectForm').submit();
            </script>
        </body>
        </html>
        """.format(aadhar_no))
        
        return response
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating taxation record: {str(e)}", "danger")
        return redirect(url_for('main.modify_taxation_record', aadhar_no=aadhar_no))

# Delete Taxation Record
@main_bp.route('/delete_taxation_record', methods=['POST'])
def delete_taxation_record():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        aadhar_no = request.form.get('aadhar_no')
        taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
        
        if not taxation_record:
            flash("Taxation record not found!", "danger")
            return redirect(url_for('main.manage_taxation_data'))
        
        db.session.delete(taxation_record)
        db.session.commit()
                
        # Redirect back to the find taxation records page
        return redirect(url_for('main.find_taxation_records'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting taxation record: {str(e)}", "danger")
        return redirect(url_for('main.find_taxation_records'))

# Add/ View/ Delete/ Modify Meetings
@main_bp.route('/manage_meeting_details', methods=['GET', 'POST']) # flag 
def manage_meeting_details():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add meeting details logic
            new_meeting = Meetings(
                date_conducted=request.form.get('date_conducted'),
                meeting_agenda=request.form.get('meeting_agenda')
            )
            db.session.add(new_meeting)
            db.session.commit()

        elif action == 'delete':
            # Delete meeting details logic
            meeting_id = request.form.get('meeting_id')
            meeting = Meetings.query.filter_by(meeting_id=meeting_id).first()
            if meeting:
                db.session.delete(meeting)
                db.session.commit()
            else:
                flash("Meeting not found!", "danger")
                return redirect(url_for('main.manage_meeting_details'))

    meetings_list = Meetings.query.all()
    return render_template('manage_meeting_details.html', meetings=meetings_list)

# Add/ View/ Delete/ Modify Complaints
@main_bp.route('/manage_complaints', methods=['GET', 'POST'])
def manage_complaints():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            # Delete complaint logic
            complaint_id = request.form.get('complaint_id')
            
            # Find the complaint by ID
            complaint = Complaints.query.filter_by(complaint_id=complaint_id).first()
            if complaint:
                db.session.delete(complaint)
                db.session.commit()
            else:
                flash("Complaint not found!", "danger")

    # Query to get complaint details along with citizen and resource names
    complaints_list = db.session.query(
        Complaints.complaint_id,
        Resources.resource_name,
        Citizens.name.label('citizen_name'),
        Complaints.complaint_desc,
        Complaints.complain_date
    ).join(Citizens, Citizens.aadhar_no == Complaints.aadhar_no) \
     .join(Resources, Resources.resource_id == Complaints.resource_id) \
     .all()

    return render_template('manage_complaints.html', complaints=complaints_list)

# Add/ View/ Delete/ Modify Resources
@main_bp.route('/manage_resources', methods=['GET', 'POST'])
def manage_resources():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            resource_name = request.form.get('resource_name')
            existing_resource = db.session.execute(
                text("SELECT * FROM Resources WHERE Resource_Name = :resource_name"),
                {'resource_name': resource_name}
            ).fetchone()

            if existing_resource:
                flash("A resource with this name already exists in the database!", "danger")
                return redirect(url_for('main.manage_resources'))
            else:
                new_resource = Resources(
                    resource_name=resource_name,
                    last_inspected_date=request.form.get('last_inspected_date')
                )
                db.session.add(new_resource)
                db.session.commit()

        elif action == 'delete':
            # Delete resource logic
            resource_id = request.form.get('resource_id')
            resource = Resources.query.filter_by(resource_id=resource_id).first()
            if resource:
                db.session.delete(resource)
                db.session.commit()
            else:
                flash("Resource not found!", "danger")

        elif action == 'edit':
            # Edit resource logic
            resource_id = request.form.get('resource_id')
            new_inspection_date = request.form.get('last_inspected_date')
            resource = Resources.query.filter_by(resource_id=resource_id).first()
            if resource:
                resource.last_inspected_date = new_inspection_date
                db.session.commit()
            else:
                flash("Resource not found!", "danger")

    # Fetch all resources for display
    resources_list = Resources.query.all()
    return render_template('manage_resources.html', resources=resources_list)

# Add Government Institution
@main_bp.route('/add_government_institution', methods=['GET', 'POST'])
def add_government_institution():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    errors = {}
    form_data = {
        'institute_type': '',
        'institute_name': '',
        'institute_location': ''
    }
    
    if request.method == 'POST':
        try:
            form_data['institute_type'] = request.form.get('institute_type', '')
            form_data['institute_name'] = request.form.get('institute_name', '')
            form_data['institute_location'] = request.form.get('institute_location', '')
            
            # Validate required fields
            if not form_data['institute_type']:
                errors['institute_type'] = "Institution type is required!"
            if not form_data['institute_name']:
                errors['institute_name'] = "Institution name is required!"
            if not form_data['institute_location']:
                errors['institute_location'] = "Institution location is required!"
            
            # Validate institute_type
            valid_types = ['Educational', 'Health', 'Banking', 'Administration']
            if form_data['institute_type'] and form_data['institute_type'] not in valid_types:
                errors['institute_type'] = "Invalid institution type!"
            
            # If no errors, proceed with insertion
            if not errors:
                # Check if institution with same name already exists
                existing = db.session.execute(
                    text("SELECT * FROM Government_Institutions WHERE Institute_Name = :name AND Institute_Type = :type"),
                    {'name': form_data['institute_name'], 'type': form_data['institute_type']}
                ).fetchone()
                
                if existing:
                    errors['institute_name'] = "An institution with this name already exists!"
                else:
                    # Insert into Government_Institutions table
                    db.session.execute(
                        text("""
                        INSERT INTO Government_Institutions (Institute_Type, Institute_Name, Institue_Location)
                        VALUES (:institute_type, :institute_name, :institute_location)
                        """),
                        {
                            'institute_type': form_data['institute_type'],
                            'institute_name': form_data['institute_name'],
                            'institute_location': form_data['institute_location']
                        }
                    )
                    db.session.commit()
                    return redirect(url_for('main.view_government_bodies'))
                    
        except Exception as e:
            db.session.rollback()
            errors['general'] = f"An error occurred: {str(e)}"
    
    # Get all institutions for display
    institutions = db.session.execute(text("SELECT * FROM Government_Institutions")).fetchall()
    
    # Render template with form data, errors, and institutions
    return render_template('view_government_bodies.html', 
                          institutions=institutions,
                          form_data=form_data,
                          errors=errors)

# Delete Government Institution (by name and type)
@main_bp.route('/delete_government_institution/<institute_type>/<institute_name>', methods=['POST'])
def delete_government_institution(institute_type, institute_name):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        # Check if institution exists with both name and type
        institution = db.session.execute(
            text("SELECT * FROM Government_Institutions WHERE Institute_Name = :name AND Institute_Type = :type"),
            {'name': institute_name, 'type': institute_type}
        ).fetchone()
        
        if institution:
            # Delete the institution matching both name and type
            db.session.execute(
                text("DELETE FROM Government_Institutions WHERE Institute_Name = :name AND Institute_Type = :type"),
                {'name': institute_name, 'type': institute_type}
            )
            db.session.commit()
            flash(f"Institution '{institute_name}' of type '{institute_type}' deleted successfully!", "success")
        else:
            flash(f"Institution '{institute_name}' of type '{institute_type}' not found!", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting institution: {str(e)}", "danger")
    
    return redirect(url_for('main.view_government_bodies'))

# View Government Institutions
@main_bp.route('/view_government_bodies')
def view_government_bodies():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    # Get all institutions for display
    institutions = db.session.execute(text("SELECT * FROM Government_Institutions")).fetchall()
    
    return render_template('view_government_bodies.html', institutions=institutions)

# Add beneficiary to welfare scheme
@main_bp.route('/avail_welfare_scheme', methods=['GET'])
def avail_welfare_scheme():
    # Fetch all welfare schemes from the database
    schemes = db.session.execute(
        text("SELECT Scheme_ID, Scheme_Type, Scheme_Description FROM Welfare_Schemes ORDER BY Scheme_ID")
    ).fetchall()
    
    return render_template('avail_welfare_scheme.html', schemes=schemes)

# Submit welfare scheme
@main_bp.route('/submit_scheme', methods=['POST'])
def submit_scheme():
    try:
        scheme_id = request.form.get('scheme_id')
        citizen_aadhar_no = request.form.get('citizen_aadhar_no')

        if not scheme_id or not citizen_aadhar_no:
            flash("Both Scheme ID and Aadhar Number are required!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Convert scheme_id to integer
        try:
            scheme_id = int(scheme_id)
        except ValueError:
            flash("Invalid Scheme ID format!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Check if scheme exists
        scheme = Welfare_Schemes.query.get(scheme_id)
        if not scheme:
            flash("Invalid Scheme ID!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=citizen_aadhar_no).first()
        if not citizen:
            flash("Invalid Aadhar Number!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        if not citizen.is_alive:
            flash("Citizen is not alive!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))
        
        # Check if already availed
        existing_avail = db.session.execute(text("""
            SELECT * FROM Avails 
            WHERE Aadhar_No = :aadhar_no AND Scheme_ID = :scheme_id
        """), {'aadhar_no': citizen_aadhar_no, 'scheme_id': scheme_id}).fetchone()

        if existing_avail:
            flash("This citizen has already availed this scheme!", "warning")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Insert into Avails table
        db.session.execute(text("""
            INSERT INTO Avails (Aadhar_No, Scheme_ID, Avail_Date) 
            VALUES (:aadhar_no, :scheme_id, CURRENT_DATE)
        """), {'aadhar_no': citizen_aadhar_no, 'scheme_id': scheme_id})

        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('main.avail_welfare_scheme'))

# Remove beneficiary from welfare scheme
@main_bp.route('/remove_scheme_beneficiary', methods=['POST'])
def remove_scheme_beneficiary():
    try:
        scheme_id = request.form.get('scheme_id')
        citizen_aadhar_no = request.form.get('citizen_aadhar_no')

        if not scheme_id or not citizen_aadhar_no:
            flash("Both Scheme ID and Aadhar Number are required!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Convert scheme_id to integer
        try:
            scheme_id = int(scheme_id)
        except ValueError:
            flash("Invalid Scheme ID format!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Check if the scheme and citizen exist in Avails table
        availed_scheme = db.session.execute(text("""
            SELECT * FROM Avails 
            WHERE Aadhar_No = :aadhar_no AND Scheme_ID = :scheme_id
        """), {'aadhar_no': citizen_aadhar_no, 'scheme_id': scheme_id}).fetchone()

        if not availed_scheme:
            flash("No record found for the given Scheme ID and Aadhar Number!", "danger")
            return redirect(url_for('main.avail_welfare_scheme'))

        # Remove the record
        db.session.execute(text("""
            DELETE FROM Avails 
            WHERE Aadhar_No = :aadhar_no AND Scheme_ID = :scheme_id
        """), {'aadhar_no': citizen_aadhar_no, 'scheme_id': scheme_id})

        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('main.avail_welfare_scheme'))

# Submit a complaint from citizen
@main_bp.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        aadhar_no = request.form.get('aadhar_no')
        resource_id = request.form.get('resource_id')
        complaint_desc = request.form.get('complaint_desc')
        
        if not aadhar_no or not resource_id or not complaint_desc:
            flash("All fields are required for submitting a complaint!", "danger")
            return redirect(url_for('main.citizen', aadhar_no=aadhar_no))
        
        # Check if resource exists
        resource = Resources.query.get(resource_id)
        if not resource:
            flash("Invalid Resource ID!", "danger")
            return redirect(url_for('main.citizen', aadhar_no=aadhar_no))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Invalid Aadhar Number!", "danger")
            return redirect(url_for('main.login'))
        
        # Insert into Complaints table
        db.session.execute(
            text("""
            INSERT INTO Complaints (Resource_ID, Aadhar_No, Complaint_Desc, Complain_Date)
            VALUES (:resource_id, :aadhar_no, :complaint_desc, CURRENT_DATE)
            """),
            {
                'resource_id': resource_id, 
                'aadhar_no': aadhar_no, 
                'complaint_desc': complaint_desc
            }
        )
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('main.citizen', aadhar_no=aadhar_no))


@main_bp.route('/about_us', methods=['GET'])
def about_us():
    # Fetch panchayat employees with their details, ordered by designation
    # First Sarpanch, then Naib Sarpanch, then others
    
    panchayat_employees = []
    
    # Get Sarpanch first
    sarpanch_data = db.session.execute(text("""
        SELECT c.Name, p.Designation, c.Phone_No, h.Address
        FROM Panchayat_Users p
        JOIN Citizens c ON p.Aadhar_No = c.Aadhar_No
        JOIN Household h ON c.House_No = h.House_No
        WHERE p.Designation = 'Sarpanch'
    """)).fetchall()
    
    # Get Naib Sarpanch second
    naib_sarpanch_data = db.session.execute(text("""
        SELECT c.Name, p.Designation, c.Phone_No, h.Address
        FROM Panchayat_Users p
        JOIN Citizens c ON p.Aadhar_No = c.Aadhar_No
        JOIN Household h ON c.House_No = h.House_No
        WHERE p.Designation = 'Naib Sarpanch'
    """)).fetchall()
    
    # Get other panchayat employees
    other_employees_data = db.session.execute(text("""
        SELECT c.Name, p.Designation, c.Phone_No, h.Address
        FROM Panchayat_Users p
        JOIN Citizens c ON p.Aadhar_No = c.Aadhar_No
        JOIN Household h ON c.House_No = h.House_No
        WHERE p.Designation NOT IN ('Sarpanch', 'Naib Sarpanch')
        ORDER BY p.Designation
    """)).fetchall()
    
    # Process the results into a list of dictionaries for the template
    for employee_data in sarpanch_data + naib_sarpanch_data + other_employees_data:
        panchayat_employees.append({
            'name': employee_data[0],
            'designation': employee_data[1],
            'contact_no': employee_data[2],
            'address': employee_data[3]
        })
    
    return render_template('aboutus.html', panchayat_employees=panchayat_employees)

# Declare a citizen as deceased
@main_bp.route('/declare_death', methods=['GET'])
def declare_death():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('declare_death.html')

# Process death declaration
@main_bp.route('/process_death_declaration', methods=['POST'])
def process_death_declaration():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        aadhar_no = request.form.get('aadhar_no')
        death_date = request.form.get('death_date')
        
        if not aadhar_no or not death_date:
            flash("Both Aadhar Number and Death Date are required!", "danger")
            return redirect(url_for('main.declare_death'))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar Number does not exist!", "danger")
            return redirect(url_for('main.declare_death'))
        
        # Check if citizen is already marked as deceased
        if not citizen.is_alive:
            flash("This citizen is already marked as deceased!", "warning")
            return redirect(url_for('main.declare_death'))
        
        # 1. Update citizen's is_alive status to False
        db.session.execute(
            text("""
            UPDATE Citizens
            SET Is_Alive = FALSE
            WHERE Aadhar_No = :aadhar_no
            """),
            {'aadhar_no': aadhar_no}
        )
        
        # 2. Add a death certificate
        db.session.execute(
            text("""
            INSERT INTO Certificates (Aadhar_No, Certificate_Type, Date_of_Issue)
            VALUES (:aadhar_no, 'Death', :death_date)
            """),
            {'aadhar_no': aadhar_no, 'death_date': death_date}
        )
        
        # 3. Remove the panchayat user entry
        db.session.execute(
           text("""
            DELETE FROM Panchayat_Users WHERE Aadhar_No = :aadhar_no
            """),
           {'aadhar_no': aadhar_no}
        )
        
        # 4. Remove the beneficiary
        db.session.execute(
            text("""
                 DELETE FROM Avails WHERE Aadhar_No = :aadhar_no
                 """),
            {'aadhar_no': aadhar_no}
        )
        
        # 5. Remove the complaints
        db.session.execute(
            text("""
                 DELETE FROM Complaints WHERE Aadhar_No = :aadhar_no
                 """),
            {'aadhar_no': aadhar_no}
        )
        
        # 6. Delete tax data
        db.session.execute(
            text("""
                 DELETE FROM Taxation WHERE Aadhar_No = :aadhar_no
                 """),
            {'aadhar_no': aadhar_no}
        )
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('main.dashboard_employees'))

# View beneficiaries of a welfare scheme
@main_bp.route('/scheme_beneficiaries/<int:scheme_id>', methods=['GET'])
def scheme_beneficiaries(scheme_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    # Get scheme details
    scheme = Welfare_Schemes.query.get(scheme_id)
    if not scheme:
        flash("Welfare scheme not found!", "danger")
        return redirect(url_for('main.welfare_schemes'))
    
    # Get beneficiaries with their names
    beneficiaries = db.session.execute(
        text("""
        SELECT a.Aadhar_No, c.Name, a.Avail_Date
        FROM Avails a
        JOIN Citizens c ON a.Aadhar_No = c.Aadhar_No
        WHERE a.Scheme_ID = :scheme_id
        ORDER BY a.Avail_Date DESC
        """),
        {'scheme_id': scheme_id}
    ).fetchall()
    
    # Convert to list of dictionaries for template
    beneficiaries_list = []
    for b in beneficiaries:
        beneficiaries_list.append({
            'aadhar_no': b[0],
            'name': b[1],
            'avail_date': b[2]
        })
    
    return render_template(
        'scheme_beneficiaries.html',
        scheme=scheme,
        beneficiaries=beneficiaries_list
    )
    
# Add/ View/ Delete/ Modify Households
@main_bp.route('/manage_households', methods=['GET', 'POST'])
def manage_households():
    if request.method == 'POST':
        house_no = request.form.get('house_no')
        address = request.form.get('address')

        if not address:
            flash("Address is required.", "danger")
            return jsonify({'status': 'error', 'message': "Address is required.", 'category': 'danger'})

        if house_no and house_no.strip():  # Updating an existing household
            household = Household.query.filter_by(house_no=house_no).first()
            if household:
                household.address = address
                try:
                    db.session.commit()
                    flash("Household updated successfully.", "success")
                    return jsonify({'status': 'success', 'message': "Household updated successfully.", 'category': 'success'})
                except Exception as e:
                    db.session.rollback()
                    return jsonify({'status': 'error', 'message': f"Error updating household: {str(e)}", 'category': 'danger'})
            else:
                return jsonify({'status': 'error', 'message': "Household not found.", 'category': 'danger'})
        else:  # Adding a new household
            new_household = Household(address=address)
            db.session.add(new_household)
            try:
                db.session.commit()
                flash("Household added successfully.", "success")
                return jsonify({'status': 'success', 'message': "Household added successfully.", 'category': 'success'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': f"Error adding household: {str(e)}", 'category': 'danger'})

    # Query to get households and their resident count
    sql_query = """
        SELECT h.house_no, h.address, COUNT(c.aadhar_no) as residents_count
        FROM household h
        LEFT JOIN citizens c ON h.house_no = c.house_no
        GROUP BY h.house_no, h.address
        ORDER BY h.house_no;
    """
    
    result = db.session.execute(text(sql_query))
    households = result.fetchall()

    return render_template('manage_households.html', households=households)

# Delete Household
@main_bp.route('/delete_household/<int:house_no>', methods=['POST'])
def delete_household(house_no):
    household = Household.query.get(house_no)

    if not household:
        return jsonify({'status': 'error', 'message': "Household not found.", 'category': 'danger'})

    associated_citizens = Citizens.query.filter_by(house_no=house_no).all()
    if associated_citizens and len(associated_citizens) > 0:
        return jsonify({'status': 'error', 'message': "Cannot delete household because citizens are living in it.", 'category': 'danger'})

    try:
        db.session.delete(household)
        db.session.commit()
        return jsonify({'status': 'success', 'message': "Household deleted successfully.", 'category': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f"Error deleting household: {str(e)}", 'category': 'danger'})

# Add this route in routes.py
@main_bp.route('/execute_sql', methods=['GET', 'POST'])
def execute_sql():
    if 'user' not in session or session.get('user_type') != 'System Administrator':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.login'))

    query = ""
    result = None
    error = None

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            try:
                result_proxy = db.session.execute(text(query))
                if result_proxy.returns_rows:
                    result = [dict(row._mapping) for row in result_proxy.fetchall()]
                else:
                    db.session.commit()
                    result = f"Query executed successfully. Rows affected: {result_proxy.rowcount}"
            except Exception as e:
                db.session.rollback()
                error = str(e)

    return render_template('execute_sql.html', query=query, result=result, error=error)
