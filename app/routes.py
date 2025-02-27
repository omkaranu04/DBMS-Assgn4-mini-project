from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import LoginForm, PanchayatEmployeeForm, GovernmentOfficialForm
from .models import SystemUsersTop, PanchayatUsers, Citizens
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
                session['user'] = username  # Store session info for logged-in user.
                return redirect(url_for('main.dashboard'))
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
@main_bp.route('/add_edit_panchayat_employee/<username>', methods=['GET', 'POST'])
def add_edit_panchayat_employee(username=None):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    form = PanchayatEmployeeForm()
    employee = None

    if username:  # Editing an existing employee
        employee = PanchayatUsers.query.filter_by(username=username).first()
        if employee:
            form.username.data = employee.username
            form.password.data = employee.password  # Pre-fill password (optional)
            form.designation.data = employee.designation

    if form.validate_on_submit():
        if employee:  # Update existing employee
            employee.username = form.username.data.strip()
            employee.password = form.password.data.strip()
            employee.designation = form.designation.data.strip()
            flash('Panchayat Employee updated successfully!', 'success')
        else:  # Add new employee
            new_employee = PanchayatUsers(
                username=form.username.data.strip(),
                password=form.password.data.strip(),
                designation=form.designation.data.strip()
            )
            db.session.add(new_employee)
            flash('Panchayat Employee added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('main.panchayat_employees'))

    return render_template('add_edit_panchayat_employee.html', form=form)

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
@main_bp.route('/add_edit_government_official/<username>', methods=['GET', 'POST'])
def add_edit_government_official(username=None):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    form = GovernmentOfficialForm()
    official = None

    # Check if username is provided and fetch existing official
    if username:
        official = SystemUsersTop.query.filter_by(username=username).first()
        if official:
            form.username.data = official.username
            form.password.data = official.password  # Pre-fill password (if needed)

    if form.validate_on_submit():
        if official:  # Update existing official
            official.username = form.username.data.strip()
            official.password = form.password.data.strip()
            flash('Government Official updated successfully!', 'success')
        else:  # Add new official
            new_official = SystemUsersTop(
                username=form.username.data.strip(),
                password=form.password.data.strip(),
                user_type='Government Official'
            )
            db.session.add(new_official)
            flash('Government Official added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('main.government_officials'))

    return render_template('add_edit_government_official.html', form=form)


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
