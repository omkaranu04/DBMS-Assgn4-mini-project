from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import LoginForm, PanchayatEmployeeForm, GovernmentOfficialForm
from .models import SystemUsersTop, PanchayatUsers, Citizens, Certificates, Welfare_Schemes, Agricultural_Land, Health_CheckUp, Taxation, Meetings, Complaints, Household, Resources, Government_Institutions
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

    employees = PanchayatUsers.query.all()
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

        # Aadhar number remains unchanged
        form_aadhar_no = request.form.get('aadhar_no', form_aadhar_no).strip()

        # Validation checks
        if not form_username or not form_designation:
            flash('Username and designation are required!', 'danger')
        else:
            if username:  # Editing existing employee
                update_password = form_password if form_password else old_password
                password_message = "Password kept the same!" if not form_password else "Password updated successfully!"

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
        'password': "",  # Always keep blank
        'designation': form_designation,
        'aadhar_no': form_aadhar_no  # This should be disabled in the form
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

    return render_template(
        'taxation.html',
        not_paid_tax_count=not_paid_tax_count,
        people_not_paid_tax=people_not_paid_tax,
        tax_summary=tax_summary,
    )

@main_bp.route('/health', methods=['GET'])
def health():
    # Disease-specific count chart for this month
    disease_data = db.session.execute(text("""
        SELECT Medical_Condition, COUNT(*) 
        FROM Health_CheckUp 
        WHERE EXTRACT(MONTH FROM Date_of_Visit) = EXTRACT(MONTH FROM CURRENT_DATE)
          AND EXTRACT(YEAR FROM Date_of_Visit) = EXTRACT(YEAR FROM CURRENT_DATE)
        GROUP BY Medical_Condition
    """)).fetchall()

    return render_template('health.html', disease_data=disease_data)

@main_bp.route('/welfare_schemes', methods=['GET'])
def welfare_schemes():
    schemes = db.session.execute(text("SELECT * FROM Welfare_Schemes")).fetchall()
    
    return render_template('welfare_schemes.html', schemes=schemes)

@main_bp.route('/agriculture_data', methods=['GET'])
def agriculture_data():
    # Total land area under cultivation
    total_land_area = db.session.execute(text("SELECT SUM(Area_in_Acres) FROM Agricultural_Land")).scalar()

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
    institution_counts = db.session.execute(text("""
       SELECT Institute_Type, COUNT(*)
       FROM Government_Institutions 
       GROUP BY Institute_Type;
    """)).fetchall()
    
    return render_template('institutions.html', institution_counts=institution_counts)



@main_bp.route('/dashboard_employees', methods=['GET'])
def dashboard_employees():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    return render_template('dashboard_employees.html')


@main_bp.route('/manage_citizens', methods=['GET', 'POST'])
def manage_citizens():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add citizen logic
            aadhar_no = request.form.get('aadhar_no')
            name = request.form.get('name')
            dob = request.form.get('dob')
            gender = request.form.get('gender')
            house_no = request.form.get('house_no')
            phone_no = request.form.get('phone_no')
            email_id = request.form.get('email_id')
            education_level = request.form.get('education_level')
            income = request.form.get('income')
            employment = request.form.get('employment')
            is_alive = bool(request.form.get('is_alive'))

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
            db.session.commit()
            flash("Citizen added successfully!", "success")

        elif action == 'delete':
            # Delete citizen logic
            aadhar_no = request.form.get('aadhar_no')
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            if citizen:
                db.session.delete(citizen)
                db.session.commit()
                flash("Citizen deleted successfully!", "success")
            else:
                flash("Citizen not found!", "danger")

        elif action == 'modify':
            # Modify citizen logic
            aadhar_no = request.form.get('aadhar_no')
            citizen = Citizens.query.filter_by(aadhar_no=aadhar_no).first()
            if citizen:
                citizen.name = request.form.get('name') or citizen.name
                citizen.dob = request.form.get('dob') or citizen.dob
                citizen.gender = request.form.get('gender') or citizen.gender
                citizen.house_no = request.form.get('house_no') or citizen.house_no
                citizen.phone_no = request.form.get('phone_no') or citizen.phone_no
                citizen.email_id = request.form.get('email_id') or citizen.email_id
                citizen.education_level = request.form.get('education_level') or citizen.education_level
                citizen.income = request.form.get('income') or citizen.income
                citizen.employment = request.form.get('employment') or citizen.employment
                citizen.is_alive = bool(request.form.get('is_alive')) if 'is_alive' in request.form else citizen.is_alive

                db.session.commit()
                flash("Citizen modified successfully!", "success")
            else:
                flash("Citizen not found!", "danger")

    citizens_list = Citizens.query.all()
    return render_template('manage_citizens.html', citizens=citizens_list)

@main_bp.route('/manage_certificates', methods=['GET', 'POST'])
def manage_certificates():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add certificate logic
            new_certificate = Certificates(
                aadhar_no=request.form.get('aadhar_no'),
                certificate_type=request.form.get('certificate_type'),
                date_of_issue=request.form.get('date_of_issue')
            )
            db.session.add(new_certificate)
            db.session.commit()
            flash("Certificate added successfully!", "success")

        elif action == 'delete':
            # Delete certificate logic
            certificate_id = request.form.get('certificate_id')
            certificate = Certificates.query.filter_by(certificate_id=certificate_id).first()
            if certificate:
                db.session.delete(certificate)
                db.session.commit()
                flash("Certificate deleted successfully!", "success")
            else:
                flash("Certificate not found!", "danger")

        elif action == 'modify':
            # Modify certificate logic
            certificate_id = request.form.get('certificate_id')
            certificate = Certificates.query.filter_by(certificate_id=certificate_id).first()
            if certificate:
                certificate.certificate_type = request.form.get('certificate_type') or certificate.certificate_type
                certificate.date_of_issue = request.form.get('date_of_issue') or certificate.date_of_issue
                db.session.commit()
                flash("Certificate modified successfully!", "success")
            else:
                flash("Certificate not found!", "danger")

    certificates_list = Certificates.query.all()
    return render_template('manage_certificates.html', certificates=certificates_list)

@main_bp.route('/manage_welfare_schemes', methods=['GET', 'POST'])
def manage_welfare_schemes():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add welfare scheme logic
            new_scheme = Welfare_Schemes(
                scheme_type=request.form.get('scheme_type'),
                budget=request.form.get('budget'),
                scheme_description=request.form.get('description')
            )
            db.session.add(new_scheme)
            db.session.commit()
            flash("Welfare Scheme added successfully!", "success")

        elif action == 'delete':
            # Delete welfare scheme logic
            scheme_id = request.form.get('scheme_id')
            scheme = Welfare_Schemes.query.filter_by(scheme_id=scheme_id).first()
            if scheme:
                db.session.delete(scheme)
                db.session.commit()
                flash("Welfare Scheme deleted successfully!", "success")
            else:
                flash("Welfare Scheme not found!", "danger")

        elif action == 'modify':
            # Modify welfare scheme logic
            scheme_id = request.form.get('scheme_id')
            scheme = Welfare_Schemes.query.filter_by(scheme_id=scheme_id).first()
            if scheme:
                scheme.scheme_type = request.form.get('new_scheme_type') or scheme.scheme_type
                scheme.budget = request.form.get('new_budget') or scheme.budget
                scheme.scheme_description = request.form.get('new_description') or scheme.scheme_description
                db.session.commit()
                flash("Welfare Scheme modified successfully!", "success")
            else:
                flash("Welfare Scheme not found!", "danger")

    schemes_list = Welfare_Schemes.query.all()
    return render_template('manage_welfare_schemes.html', schemes=schemes_list)

@main_bp.route('/manage_agriculture_land', methods=['GET', 'POST'])
def manage_agriculture_land():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add agriculture land logic
            new_land = Agricultural_Land(
                aadhar_no=request.form.get('aadhar_no'),
                area_in_acres=request.form.get('area_in_acres'),
                crop_type=request.form.get('crop_type'),
                soil_type=request.form.get('soil_type')
            )
            db.session.add(new_land)
            db.session.commit()
            flash("Agriculture Land added successfully!", "success")

        elif action == 'delete':
            # Delete agriculture land logic
            land_id = request.form.get('land_id')
            land = Agricultural_Land.query.filter_by(land_id=land_id).first()
            if land:
                db.session.delete(land)
                db.session.commit()
                flash("Agriculture Land deleted successfully!", "success")
            else:
                flash("Agriculture Land not found!", "danger")

        elif action == 'modify':
            # Modify agriculture land logic
            land_id = request.form.get('land_id')
            land = Agricultural_Land.query.filter_by(land_id=land_id).first()
            if land:
                land.area_in_acres = request.form.get('area_in_acres') or land.area_in_acres
                land.crop_type = request.form.get('crop_type') or land.crop_type
                land.soil_type = request.form.get('soil_type') or land.soil_type
                db.session.commit()
                flash("Agriculture Land modified successfully!", "success")
            else:
                flash("Agriculture Land not found!", "danger")

    lands_list = Agricultural_Land.query.all()
    return render_template('manage_agriculture_land.html', lands=lands_list)

@main_bp.route('/manage_health_data', methods=['GET', 'POST'])
def manage_health_data():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add health data logic
            new_health_data = Health_CheckUp(
                aadhar_no=request.form.get('aadhar_no'),
                medical_condition=request.form.get('medical_condition'),
                prescription=request.form.get('prescription'),
                date_of_visit=request.form.get('date_of_visit')
            )
            db.session.add(new_health_data)
            db.session.commit()
            flash("Health data added successfully!", "success")

        elif action == 'delete':
            # Delete health data logic
            checkup_id = request.form.get('checkup_id')
            health_data = Health_CheckUp.query.filter_by(checkup_id=checkup_id).first()
            if health_data:
                db.session.delete(health_data)
                db.session.commit()
                flash("Health data deleted successfully!", "success")
            else:
                flash("Health data not found!", "danger")

    health_list = Health_CheckUp.query.all()
    return render_template('manage_health_data.html', health=health_list)

@main_bp.route('/manage_taxation_data', methods=['GET', 'POST'])
def manage_taxation_data():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            # Add taxation data logic
            new_tax = Taxation(
                aadhar_no=request.form.get('aadhar_no'),
                tax_amount=request.form.get('tax_amount'),
                payment_status=bool(request.form.get('payment_status'))
            )
            db.session.add(new_tax)
            db.session.commit()
            flash("Taxation data added successfully!", "success")

        elif action == 'delete':
            # Delete taxation data logic
            aadhar_no = request.form.get('aadhar_no')
            tax = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
            if tax:
                db.session.delete(tax)
                db.session.commit()
                flash("Taxation data deleted successfully!", "success")
            else:
                flash("Taxation data not found!", "danger")

        elif action == 'modify':
            # Modify taxation data logic
            aadhar_no = request.form.get('aadhar_no')
            tax = Taxation.query.filter_by(aadhar_no=aadhar_no).first()
            if tax:
                tax.tax_amount = request.form.get('tax_amount') or tax.tax_amount
                tax.payment_status = bool(request.form.get('payment_status')) if 'payment_status' in request.form else tax.payment_status
                db.session.commit()
                flash("Taxation data modified successfully!", "success")
            else:
                flash("Taxation data not found!", "danger")

    taxation_list = Taxation.query.all()
    return render_template('manage_taxation_data.html', taxation=taxation_list)

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
            # Delete complaint logic with password confirmation
            complaint_id = request.form.get('complaint_id')
            password = request.form.get('password')
            
            # Validate password (this is just an example, replace with real validation)
            if password == session['user_password']:
                complaint = Complaints.query.filter_by(complaint_id=complaint_id).first()
                if complaint:
                    db.session.delete(complaint)
                    db.session.commit()
                    flash("Complaint deleted successfully!", "success")
                else:
                    flash("Complaint not found!", "danger")
            else:
                flash("Incorrect password!", "danger")

    complaints_list = Complaints.query.all()
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
            # Delete resource logic with password confirmation
            resource_id = request.form.get('resource_id')
            resource = Resources.query.filter_by(resource_id=resource_id).first()
            if resource:
                db.session.delete(resource)
                db.session.commit()
                flash("Resource deleted successfully!", "success")
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
        
        flash("Complaint submitted successfully!", "success")
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
