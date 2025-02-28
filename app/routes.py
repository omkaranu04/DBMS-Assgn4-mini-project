from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response
from .forms import LoginForm, PanchayatEmployeeForm, GovernmentOfficialForm
from .models import SystemUsersTop, PanchayatUsers, Citizens, Certificates, Welfare_Schemes, Agricultural_Land, Health_CheckUp, Taxation, Meetings, Complaints, Household, Resources, Government_Institutions
from sqlalchemy import text, true
from . import db
from datetime import datetime
import re

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
            
            if user and user.password == password:
                session['user'] = username  # Store session info for logged-in user.
                
                # Check user_type and redirect accordingly
                if user_type == 'System Administrator':
                    return redirect(url_for('main.dashboard_administrator'))
                elif user_type == 'Government Official':
                    return redirect(url_for('main.dashboard_official'))
            else:
                flash('Invalid credentials for System Administrator or Government Official.', 'danger')
                return redirect(url_for('main.login'))

        elif user_type == 'Panchayat Employee':
            user = PanchayatUsers.query.filter_by(username=username).first()
            
            if user and user.password == password:
                session['user'] = username  # Store session info for logged-in user.
                return redirect(url_for('main.dashboard_employees'))
            else:
                flash('Invalid credentials for Panchayat Employee.', 'danger')
                return redirect(url_for('main.login'))

        elif user_type == 'Citizen':
            citizen_user = Citizens.query.filter_by(aadhar_no=username).first()
            
            if citizen_user:                                                                                            
                expected_password = f"{username[:4]}@{citizen_user.phone_no[-4:]}"
                if password == expected_password:
                    session['user'] = username  # Store session info for logged-in user.
                    return redirect(url_for('main.citizen', aadhar_no=username))
            
            flash('Invalid credentials for Citizen.', 'danger')
            return redirect(url_for('main.login'))

        else:
            flash('Invalid User Type selected.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)


@main_bp.route('/dashboard_administrator')
def dashboard_administrator():
    if 'user' not in session:
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

    # Initialize form variables
    form_username = ""
    form_password = ""
    form_designation = ""
    form_aadhar_no = ""
    old_password = ""

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
            form_password = ""  # Keep password field blank

    if request.method == 'POST':
        # Get form data from request
        form_username = request.form.get('username', '').strip()
        form_password = request.form.get('password', '').strip()
        form_designation = request.form.get('designation', '').strip()

        # Aadhar number remains unchanged during edit
        if not username:  # Only set aadhar number during addition
            form_aadhar_no = request.form.get('aadhar_no', '').strip()

        # Validation checks
        if not form_username or not form_designation:
            flash('Username and designation are required!', 'danger')
        elif not username and not form_password:  # Password is mandatory when adding a new user
            flash('Password is required when adding a new Panchayat Employee!', 'danger')
        else:
            if username:  # Editing existing employee
                # Fetch old password to retain if new password is blank or has only spaces
                employee_result = db.session.execute(
                    text("SELECT password FROM Panchayat_Users WHERE username = :username"),
                    {'username': username}
                ).fetchone()
                
                old_password = employee_result[0] if employee_result else ""

                # Use old password if new password is blank or contains only spaces
                update_password = form_password if form_password else old_password
                password_message = "Password updated successfully!" if form_password else "Password kept the same!"

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
                flash(f'Panchayat Employee updated successfully! {password_message}', 'success')
            else:  # Adding a new employee
                db.session.execute(
                    text("""
                        INSERT INTO Panchayat_Users (username, password, designation, aadhar_no)
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

    # Form data for rendering
    form_data = {
        'username': form_username,
        'password': "",  # Always keep blank for security reasons
        'designation': form_designation,
        'aadhar_no': form_aadhar_no  # This should be disabled in the HTML for edits
    }

    return render_template('panchayat_employees_form.html', form_data=form_data, username=username)

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

# view all Government Officials
@main_bp.route('/government_officials', methods=['GET'])
def government_officials():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    officials = SystemUsersTop.query.filter_by(user_type='Government Official').all()
    return render_template('government_officials.html', officials=officials)

# View all Government Officials
@main_bp.route('/add_edit_government_official/', defaults={'username': None}, methods=['GET', 'POST'])
@main_bp.route('/add_edit_government_official/<username>', methods=['GET', 'POST'])
def add_edit_government_official(username=None):

    if 'user' not in session:
        return redirect(url_for('main.login'))

    form = GovernmentOfficialForm()
    official = None
    old_password = ""

    if username:
        official = SystemUsersTop.query.filter_by(username=username).first()
        if official:
            form.username.data = official.username  # Prefill username
            old_password = official.password  # Store existing password
            form.password.data = ""  # Keep password field blank for security

    if request.method == 'POST':
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()

        if not username_input:
            flash("Username is required!", "danger")
            return redirect(url_for('main.add_edit_government_official', username=username))

        if official:  # Editing existing official
            if password_input:  # User entered a new password
                official.password = password_input  # Store the new password
                password_message = "Password updated successfully!"
            else:
                password_message = "Password kept the same!"

            official.username = username_input  # Update username
            flash(f"Government Official updated successfully! {password_message}", "success")

        else:  # Adding a new official
            # Ensure the username is unique
            existing_user = SystemUsersTop.query.filter_by(username=username_input).first()
            if existing_user:
                flash("Username already exists! Choose a different one.", "danger")
                return redirect(url_for('main.add_edit_government_official'))

            # Create a new official
            new_official = SystemUsersTop(
                username=username_input,
                password=password_input,  # Store password as plain text (for now)
                user_type='Government Official'
            )
            db.session.add(new_official)
            flash("Government Official added successfully!", "success")

        db.session.commit()
        return redirect(url_for('main.government_officials'))

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



@main_bp.route('/dashboard_official', methods=['GET'])
def dashboard_official():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard_official.html')

@main_bp.route('/census', methods=['GET'])
def census():
    # Total people alive now
    total_alive = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Is_Alive = TRUE")).scalar()

    # Total male
    total_male = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Gender = 'Male' AND Is_Alive = TRUE")).scalar()

    # Total female
    total_female = db.session.execute(text("SELECT COUNT(*) FROM Citizens WHERE Gender = 'Female' AND Is_Alive = TRUE")).scalar()

    # Employment status chart data
    employment_data = db.session.execute(text("""
        SELECT Employment, COUNT(*) 
        FROM Citizens 
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

    # Education level chart data
    education_data = db.session.execute(text("""
        SELECT Education_Level, COUNT(*) 
        FROM Citizens 
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
    
    # print("Not Paid Tax Count:", not_paid_tax_count)
    # print("People Not Paid Tax:", people_not_paid_tax)
    # print("Tax Summary:", tax_summary)

    return render_template(
        'taxation.html',
        not_paid_tax_count=not_paid_tax_count,
        people_not_paid_tax=people_not_paid_tax,
        tax_summary=tax_summary,
    )

@main_bp.route('/health', methods=['GET'])
def health():
    # Disease-specific count chart for this year
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



@main_bp.route('/dashboard_employees', methods=['GET'])
def dashboard_employees():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard_employees.html')


@main_bp.route('/manage_citizens', methods=['GET'])
def manage_citizens():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizens_list = Citizens.query.filter_by(is_alive=True).all()
    return render_template('manage_citizens.html', citizens=citizens_list)

@main_bp.route('/add_citizen', methods=['GET', 'POST'])
def add_citizen():
    form_data = request.form.to_dict() if request.method == 'POST' else {}
    
    if request.method == 'POST':
        # Get and strip form data
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

        # Validate required fields
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
        if phone_no and (not phone_no.isdigit() or len(phone_no) != 10 or phone_no[0] not in '69'):
            flash("Invalid phone number! It must contain only numbers, be exactly 10 digits, and start with 6 or 9.", "phone_no_error")
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
            # flash("Citizen added successfully with a birth certificate!", "success")
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
        
        flash("Citizen and all related records deleted successfully!", "success")
        return redirect(url_for('main.manage_citizens'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting citizen: {str(e)}", "danger")
        return redirect(url_for('main.delete_citizen'))

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

@main_bp.route('/modify_citizen_submit/<aadhar_no>', methods=['POST'])
def modify_citizen_submit(aadhar_no):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen not found!", "danger")
            return redirect(url_for('main.manage_citizens'))
        
        # Update citizen information
        citizen.name = request.form.get('name', '').strip()
        citizen.dob = request.form.get('dob', '').strip()
        citizen.gender = request.form.get('gender', '').strip()
        citizen.house_no = request.form.get('house_no', '').strip()
        citizen.phone_no = request.form.get('phone_no', '').strip()
        citizen.email_id = request.form.get('email_id', '').strip()
        citizen.education_level = request.form.get('education_level', '').strip()
        citizen.income = request.form.get('income', '').strip()
        citizen.employment = request.form.get('employment', '').strip()
        citizen.is_alive = citizen.is_alive  # Keep the same    
        
        db.session.commit()
        
        # flash("Citizen information updated successfully!", "success")
        return redirect(url_for('main.manage_citizens'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating citizen: {str(e)}", "danger")
        return redirect(url_for('main.modify_citizen', aadhar_no=aadhar_no))


@main_bp.route('/manage_certificates', methods=['GET'])
def manage_certificates():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_certificates.html')

@main_bp.route('/add_certificate', methods=['GET', 'POST'])
def add_certificate():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        certificate_type = request.form.get('certificate_type', '').strip()
        date_of_issue = request.form.get('date_of_issue', '').strip()
        
        # Validate inputs
        if not all([aadhar_no, certificate_type, date_of_issue]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.add_certificate'))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.add_certificate'))
        
        # Special handling for Death certificates
        if certificate_type == 'Death' and citizen.is_alive:
            # Update citizen status to deceased
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
            
            flash("Certificate added successfully!", "success")
            return redirect(url_for('main.manage_certificates'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding certificate: {str(e)}", "danger")
            return redirect(url_for('main.add_certificate'))
    
    return render_template('add_certificate.html')

@main_bp.route('/find_certificates', methods=['GET', 'POST'])
def find_certificates():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    certificates = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        if not aadhar_no:
            flash("Aadhar number is required!", "danger")
            return redirect(url_for('main.find_certificates'))
        
        # Find citizen
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.find_certificates'))
        
        # Get certificates for this citizen
        certificates = Certificates.query.filter_by(aadhar_no=aadhar_no).all()
    
    return render_template('find_certificates.html', citizen=citizen, certificates=certificates)

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

@main_bp.route('/modify_certificate_submit/<int:certificate_id>', methods=['POST'])
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
        
        # Update certificate
        certificate.certificate_type = certificate_type
        certificate.date_of_issue = date_of_issue
        
        # Special handling for Death certificates
        if certificate_type == 'Death':
            citizen = Citizens.query.filter_by(aadhar_no=certificate.aadhar_no).first()
            if citizen and citizen.is_alive:
                citizen.is_alive = False
        
        db.session.commit()
        
        flash("Certificate updated successfully!", "success")
        return redirect(url_for('main.find_certificates'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating certificate: {str(e)}", "danger")
        return redirect(url_for('main.modify_certificate', certificate_id=certificate_id))

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

@main_bp.route('/delete_certificate_confirm/<int:certificate_id>', methods=['POST'])
def delete_certificate_confirm(certificate_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        certificate = Certificates.query.get(certificate_id)
        if not certificate:
            flash("Certificate not found!", "danger")
            return redirect(url_for('main.manage_certificates'))
        
        aadhar_no = certificate.aadhar_no
        
        # Delete the certificate
        db.session.delete(certificate)
        db.session.commit()
        
        flash("Certificate deleted successfully!", "success")
        
        # Redirect back to find certificates with the same Aadhar number
        return redirect(url_for('main.find_certificates'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting certificate: {str(e)}", "danger")
        return redirect(url_for('main.delete_certificate', certificate_id=certificate_id))

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
                    flash("Welfare Scheme deleted successfully!", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error deleting scheme: {str(e)}", "danger")
            else:
                flash("Welfare Scheme not found!", "danger")
    
    # Get all welfare schemes
    schemes_list = Welfare_Schemes.query.order_by(Welfare_Schemes.scheme_id).all()
    return render_template('manage_welfare_schemes.html', schemes=schemes_list)

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
        
        try:
            # Create new welfare scheme
            new_scheme = Welfare_Schemes(
                scheme_type=scheme_type,
                budget=budget,
                scheme_description=description
            )
            
            db.session.add(new_scheme)
            db.session.commit()
            
            flash("Welfare Scheme added successfully!", "success")
            return redirect(url_for('main.manage_welfare_schemes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding welfare scheme: {str(e)}", "danger")
            return redirect(url_for('main.add_welfare_scheme'))
    
    return render_template('add_welfare_scheme.html')

@main_bp.route('/modify_welfare_scheme/<int:scheme_id>', methods=['GET'])
def modify_welfare_scheme(scheme_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    scheme = Welfare_Schemes.query.get(scheme_id)
    if not scheme:
        flash("Welfare Scheme not found!", "danger")
        return redirect(url_for('main.manage_welfare_schemes'))
    
    return render_template('modify_welfare_scheme.html', scheme=scheme)

@main_bp.route('/modify_welfare_scheme_submit/<int:scheme_id>', methods=['POST'])
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
        
        # Update scheme
        scheme.scheme_type = scheme_type
        scheme.budget = budget
        scheme.scheme_description = description
        
        db.session.commit()
        
        flash("Welfare Scheme updated successfully!", "success")
        return redirect(url_for('main.manage_welfare_schemes'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating welfare scheme: {str(e)}", "danger")
        return redirect(url_for('main.modify_welfare_scheme', scheme_id=scheme_id))

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
                    flash("Agricultural land record deleted successfully!", "success")
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
            
            flash("Agricultural land added successfully!", "success")
            return redirect(url_for('main.manage_agriculture_land'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding agricultural land: {str(e)}", "danger")
            return redirect(url_for('main.add_agriculture_land'))
    
    return render_template('add_agriculture_land.html')

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
        
        # Update land record
        land.area_in_acres = area_in_acres
        land.crop_type = crop_type
        land.soil_type = soil_type
        
        db.session.commit()
        
        flash("Agricultural land updated successfully!", "success")
        return redirect(url_for('main.manage_agriculture_land'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating agricultural land: {str(e)}", "danger")
        return redirect(url_for('main.modify_agriculture_land', land_id=land_id))

@main_bp.route('/manage_health_data', methods=['GET'])
def manage_health_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_health_data.html')

@main_bp.route('/add_health_data', methods=['GET', 'POST'])
def add_health_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        medical_condition = request.form.get('medical_condition', '').strip()
        prescription = request.form.get('prescription', '').strip()
        date_of_visit = request.form.get('date_of_visit', '').strip()
        
        # Validate inputs
        if not all([aadhar_no, medical_condition, prescription, date_of_visit]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.add_health_data'))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.add_health_data'))
        
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
            
            flash("Health record added successfully!", "success")
            return redirect(url_for('main.manage_health_data'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding health record: {str(e)}", "danger")
            return redirect(url_for('main.add_health_data'))
    
    return render_template('add_health_data.html')

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
        
        flash("Health record updated successfully!", "success")
        
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
        
        aadhar_no = record.aadhar_no
        
        db.session.delete(record)
        db.session.commit()
        
        flash("Health record deleted successfully!", "success")
        
        # Redirect back to the same citizen's records
        return redirect(url_for('main.find_health_records'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting health record: {str(e)}", "danger")
        return redirect(url_for('main.find_health_records'))

@main_bp.route('/manage_taxation_data', methods=['GET'])
def manage_taxation_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('manage_taxation_data.html')

@main_bp.route('/add_taxation_data', methods=['GET', 'POST'])
def add_taxation_data():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        tax_amount = request.form.get('tax_amount', '').strip()
        payment_status = False
        
        # Validate inputs
        if not all([aadhar_no, tax_amount]):
            flash("All fields are required!", "danger")
            return redirect(url_for('main.add_taxation_data'))
        
        # Check if citizen exists
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.add_taxation_data'))
        
        # Check if taxation record already exists for this citizen
        existing_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
        if existing_record:
            flash("Taxation record already exists for this citizen!", "danger")
            return redirect(url_for('main.add_taxation_data'))
        
        try:
            # Create new taxation record
            new_record = Taxation(
                aadhar_no=aadhar_no,
                tax_amount=tax_amount,
                payment_status=payment_status
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash("Taxation record added successfully!", "success")
            return redirect(url_for('main.manage_taxation_data'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding taxation record: {str(e)}", "danger")
            return redirect(url_for('main.add_taxation_data'))
    
    return render_template('add_taxation_data.html')

@main_bp.route('/find_taxation_records', methods=['GET', 'POST'])
def find_taxation_records():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    citizen = None
    taxation_record = None
    
    if request.method == 'POST':
        aadhar_no = request.form.get('aadhar_no', '').strip()
        
        if not aadhar_no:
            flash("Aadhar number is required!", "danger")
            return redirect(url_for('main.find_taxation_records'))
        
        # Find citizen
        citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
        if not citizen:
            flash("Citizen with this Aadhar number does not exist!", "danger")
            return redirect(url_for('main.find_taxation_records'))
        
        # Get taxation record for this citizen
        taxation_record = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
    
    return render_template('find_taxation_records.html', citizen=citizen, taxation_record=taxation_record)

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
        
        flash("Taxation record updated successfully!", "success")
        
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
        
        flash("Taxation record deleted successfully!", "success")
        
        # Redirect back to the find taxation records page
        return redirect(url_for('main.find_taxation_records'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting taxation record: {str(e)}", "danger")
        return redirect(url_for('main.find_taxation_records'))

@main_bp.route('/manage_meeting_details', methods=['GET', 'POST'])
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
            flash("Meeting details added successfully!", "success")

        elif action == 'delete':
            # Delete meeting details logic
            meeting_id = request.form.get('meeting_id')
            meeting = Meetings.query.filter_by(meeting_id=meeting_id).first()
            if meeting:
                db.session.delete(meeting)
                db.session.commit()
                flash("Meeting details deleted successfully!", "success")
            else:
                flash("Meeting not found!", "danger")

    meetings_list = Meetings.query.all()
    return render_template('manage_meeting_details.html', meetings=meetings_list)

# yet to be checked because of correlation
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
                flash("Complaint deleted successfully!", "success")
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

@main_bp.route('/manage_resources', methods=['GET', 'POST'])
def manage_resources():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # Add resource logic
            new_resource = Resources(
                resource_name=request.form.get('resource_name'),
                last_inspected_date=request.form.get('last_inspected_date')
            )
            db.session.add(new_resource)
            db.session.commit()
            flash("Resource added successfully!", "success")

        elif action == 'delete':
            # Delete resource logic
            resource_id = request.form.get('resource_id')
            resource = Resources.query.filter_by(resource_id=resource_id).first()
            if resource:
                db.session.delete(resource)
                db.session.commit()
                flash("Resource deleted successfully!", "success")
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
                flash("Resource updated successfully!", "success")
            else:
                flash("Resource not found!", "danger")

    # Fetch all resources for display
    resources_list = Resources.query.all()
    return render_template('manage_resources.html', resources=resources_list)

@main_bp.route('/view_government_bodies', methods=['GET'])
def view_government_bodies():
    # Fetch all government institutions grouped by type
    institutions = db.session.execute(text("""
        SELECT Institute_Type, Institute_Name, Institue_Location 
        FROM Government_Institutions
        ORDER BY Institute_Type, Institute_Name
    """)).fetchall()

    # Pass the data to the template for rendering
    return render_template('view_government_bodies.html', institutions=institutions)

@main_bp.route('/avail_welfare_scheme', methods=['GET'])
def avail_welfare_scheme():
    return render_template('avail_welfare_scheme.html')

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
        flash("Welfare Scheme availed successfully!", "success")
    
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('main.avail_welfare_scheme'))


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
        flash("Beneficiary removed from the welfare scheme successfully!", "success")
    
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('main.avail_welfare_scheme'))


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
        
        # flash("Complaint submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('main.citizen', aadhar_no=aadhar_no))

@main_bp.route('/add_government_institution', methods=['POST'])
def add_government_institution():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    try:
        institute_type = request.form.get('institute_type')
        institute_name = request.form.get('institute_name')
        institute_location = request.form.get('institute_location')
        
        if not institute_type or not institute_name or not institute_location:
            flash("All fields are required!", "danger")
            return redirect(url_for('main.view_government_bodies'))
        
        # Validate institute_type
        valid_types = ['Educational', 'Health', 'Banking', 'Administration']
        if institute_type not in valid_types:
            flash("Invalid institution type!", "danger")
            return redirect(url_for('main.view_government_bodies'))
        
        # Insert into Government_Institutions table
        db.session.execute(
            text("""
            INSERT INTO Government_Institutions (Institute_Type, Institute_Name, Institue_Location)
            VALUES (:institute_type, :institute_name, :institute_location)
            """),
            {
                'institute_type': institute_type,
                'institute_name': institute_name,
                'institute_location': institute_location
            }
        )
        db.session.commit()
        
        flash("Government institution added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('main.view_government_bodies'))


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

@main_bp.route('/declare_death', methods=['GET'])
def declare_death():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('declare_death.html')

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
        
        db.session.commit()
        flash("Death has been recorded successfully. Death certificate has been issued.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('main.dashboard_employees'))
