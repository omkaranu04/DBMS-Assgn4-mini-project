from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import LoginForm, PanchayatEmployeeForm, GovernmentOfficialForm
from .models import SystemUsersTop, PanchayatUsers, Citizens
from sqlalchemy import text
from . import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()
        user_type = form.user_type.data.strip()

        if user_type in ['System Administrator', 'Government Official']:
            user = SystemUsersTop.query.filter_by(username=username).first()
            if user and user.password == password and user.user_type == user_type:
                session['user'] = username  # Store session info for logged-in user.
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid credentials for System Administrator or Government Official.', 'danger')

        elif user_type == 'Panchayat Employee':
            user = PanchayatUsers.query.filter_by(username=username).first()
            if user and user.password == password:
                session['user'] = username  # Store session info for logged-in user.
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid credentials for Panchayat Employee.', 'danger')

        elif user_type == 'Citizen':
            citizen_user = Citizens.query.filter_by(aadhar_no=username).first()
            expected_password = f"{username[:4]}@{citizen_user.phone_no[-4:]}" if citizen_user else None
            if citizen_user and password == expected_password:
                session['user'] = username # Store session info for logged-in user.
                # Redirect to citizen page instead of dashboard
                return redirect(url_for('main.citizen', aadhar_no=username))
            else:
                flash('Invalid credentials for Citizen.', 'danger')


        else:
            flash('Invalid User Type selected.', 'danger')

    return render_template('login.html', form=form)

@main_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('dashboard.html')

# View all Panchayat Employees
@main_bp.route('/panchayat_employees')
def panchayat_employees():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    employees = PanchayatUsers.query.all()
    return render_template('panchayat_employees.html', employees=employees)

# Add/Edit a Panchayat Employee
@main_bp.route('/add_edit_panchayat_employee/', defaults={'username': None}, methods=['GET', 'POST'])
@main_bp.route('/add_edit_panchayat_employee/<username>', methods=['GET', 'POST'])
def add_edit_panchayat_employee(username=None):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    # Initialize variables to store form data
    form_username = ""
    form_password = ""
    form_designation = ""
    form_aadhar_no = ""

    if request.method == 'GET' and username:
        # Query existing employee data when editing
        employee_result = db.session.execute(
            text("""
                SELECT username, password, designation, aadhar_no 
                FROM PanchayatUsers 
                WHERE username = :username
            """), 
            {'username': username}
        ).fetchone()
        
        if employee_result:
            form_username = employee_result
            form_password = employee_result
            form_designation = employee_result
            form_aadhar_no = employee_result if len(employee_result) > 3 else ""

    if request.method == 'POST':
        # Get form data from request
        form_username = request.form.get('username', '').strip()
        form_password = request.form.get('password', '').strip()
        form_designation = request.form.get('designation', '').strip()
        form_aadhar_no = request.form.get('aadhar_no', '').strip()
        
        # Basic validation
        if not form_username or not form_password or not form_designation:
            flash('All fields are required!', 'danger')
        else:
            if username:  # Update existing employee
                db.session.execute(
                    text("""
                        UPDATE PanchayatUsers 
                        SET username = :username, 
                            password = :password, 
                            designation = :designation,
                            aadhar_no = :aadhar_no
                        WHERE username = :old_username
                    """), 
                    {
                        'username': form_username,
                        'password': form_password,
                        'designation': form_designation,
                        'aadhar_no': form_aadhar_no,
                        'old_username': username
                    }
                )
                flash('Panchayat Employee updated successfully!', 'success')
            else:  # Add new employee
                db.session.execute(
                    text("""
                        INSERT INTO PanchayatUsers (username, password, designation, aadhar_no)
                        VALUES (:username, :password, :designation, :aadhar_no)
                    """), 
                    {
                        'username': form_username,
                        'password': form_password,
                        'designation': form_designation,
                        'aadhar_no': form_aadhar_no
                    }
                )
                flash('Panchayat Employee added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('main.panchayat_employees'))

    # Create a dictionary to pass to the template
    form_data = {
        'username': form_username,
        'password': form_password,
        'designation': form_designation,
        'aadhar_no': form_aadhar_no
    }

    return render_template('add_edit_panchayat_employee.html', form_data=form_data, username=username)


@main_bp.route('/government_officials', methods=['GET'])
def government_officials():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    officials = SystemUsersTop.query.filter_by(user_type='Government Official').all()
    return render_template('government_officials.html', officials=officials)


# Delete a Panchayat Employee
@main_bp.route('/delete_panchayat_employee/<username>', methods=['POST'])
def delete_panchayat_employee(username):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    employee = PanchayatUsers.query.filter_by(username=username).first()
    if employee:
        db.session.delete(employee)
        db.session.commit()
        flash('Panchayat Employee deleted successfully!', 'success')

    return redirect(url_for('main.panchayat_employees'))

# View all Government Officials
@main_bp.route('/add_edit_government_official/', defaults={'username': None}, methods=['GET', 'POST'])
@main_bp.route('/add_edit_government_official/<username>', methods=['GET', 'POST'])
def add_edit_government_official(username):

    if 'user' not in session:
        return redirect(url_for('main.login'))

    form = GovernmentOfficialForm()
    official = None

    if username:
        official = SystemUsersTop.query.filter_by(username=username).first()
        if official:
            form.username.data = official.username  # Prefill username
            form.password.data = official.password  # Store password as plain text (for now)

    if request.method == 'POST':
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()

        if not username_input or not password_input:
            flash("Username and password are required!", "danger")
            return redirect(url_for('main.add_edit_government_official', username=username))

        if official:  
            # Update existing official
            official.password = password_input  # Store plain password
            flash("Government Official updated successfully!", "success")
        else:  
            # Ensure the username is unique
            existing_user = SystemUsersTop.query.filter_by(username=username_input).first()
            if existing_user:
                flash("Username already exists! Choose a different one.", "danger")
                return redirect(url_for('main.add_edit_government_official'))

            # Add new official
            new_official = SystemUsersTop(
                username=username_input,
                password=password_input,  # Store password as plain text (for now)
                user_type='Government Official'
            )
            db.session.add(new_official)
            flash("Government Official added successfully!", "success")

        db.session.commit()
        return redirect(url_for('main.government_officials'))

    return render_template('add_edit_government_official.html', form = form )

# Delete a Government Official
@main_bp.route('/delete_government_official/<username>', methods=['POST'])
def delete_government_official(username):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    official = SystemUsersTop.query.filter_by(username=username).first()
    if official:
        db.session.delete(official)
        db.session.commit()
        flash('Government Official deleted successfully!', 'success')

    return redirect(url_for('main.government_officials'))

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
        return redirect(url_for('main.dashboard'))
    
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
    
    health_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Health'
        """)
    ).fetchall()
    
    banking_institutions = db.session.execute(
        text("""
            SELECT Institute_ID, Institute_Name, Institue_Location
            FROM Government_Institutions
            WHERE Institute_Type = 'Banking'
        """)
    ).fetchall()
    
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
