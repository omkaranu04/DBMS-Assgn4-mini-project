from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import LoginForm
from .models import SystemUsersTop, PanchayatUsers, Citizens

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