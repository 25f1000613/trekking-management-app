from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import db, User, StaffProfile, Trek, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'change-this-later'

db.init_app(app)


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first.')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('You are not authorized to view this page.')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def create_admin():
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            name='Admin',
            email='admin@trek.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin account created: admin@trek.com / admin123')
    else:
        print('Admin already exists.')


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        phone_number = request.form.get('phone_number')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.')
            return redirect(url_for('register'))

        if role == 'staff':
            new_user = User(name=name, email=email,
                             password_hash=generate_password_hash(password),
                             role='staff', is_approved=False)
            db.session.add(new_user)
            db.session.commit()

            staff_profile = StaffProfile(user_id=new_user.id, phone_number=phone_number)
            db.session.add(staff_profile)
            db.session.commit()
            flash('Registration successful. Please wait for admin approval before logging in.')
        else:
            new_user = User(name=name, email=email,
                             password_hash=generate_password_hash(password),
                             role='trekker', is_approved=True)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please login.')

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.')
            return redirect(url_for('login'))

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact admin.')
            return redirect(url_for('login'))

        if user.role == 'staff' and not user.is_approved:
            flash('Your account is pending admin approval.')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['name'] = user.name
        session['role'] = user.role

        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))




@app.route('/user/dashboard')
@login_required(role='trekker')
def user_dashboard():
    return f"Welcome {session.get('name')} (dashboard coming soon)"


@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    total_treks = Trek.query.count()
    total_staff = User.query.filter_by(role='staff').count()
    total_users = User.query.filter_by(role='trekker').count()
    total_bookings = Booking.query.count()
    return render_template('admin_dashboard.html',
                            total_treks=total_treks,
                            total_staff=total_staff,
                            total_users=total_users,
                            total_bookings=total_bookings)


@app.route('/admin/treks')
@login_required(role='admin')
def admin_treks():
    query = request.args.get('q', '')
    treks_query = Trek.query
    if query:
        if query.isdigit():
            treks_query = treks_query.filter(Trek.id == int(query))
        else:
            treks_query = treks_query.filter(Trek.name.ilike(f'%{query}%'))
    treks = treks_query.all()
    return render_template('admin_treks.html', treks=treks, query=query)


@app.route('/admin/treks/add', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_add_trek():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        duration_days = int(request.form.get('duration_days'))
        total_slots = int(request.form.get('total_slots'))
        start_date_str = request.form.get('start_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = start_date + timedelta(days=duration_days) if start_date else None

        staff_id = request.form.get('staff_id')
        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            total_slots=total_slots,
            available_slots=total_slots,
            status='Pending',
            start_date=start_date,
            end_date=end_date,
            staff_id=int(staff_id) if staff_id else None
        )
        db.session.add(new_trek)
        db.session.commit()
        flash('Trek created successfully.')
        return redirect(url_for('admin_treks'))

    available_staff = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()
    return render_template('admin_trek_form.html', trek=None, available_staff=available_staff)


@app.route('/admin/treks/edit/<int:trek_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        trek.duration_days = int(request.form.get('duration_days'))
        trek.total_slots = int(request.form.get('total_slots'))
        trek.status = request.form.get('status')
        staff_id = request.form.get('staff_id')
        trek.staff_id = int(staff_id) if staff_id else None

        start_date_str = request.form.get('start_date')
        trek.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        trek.end_date = trek.start_date + timedelta(days=trek.duration_days) if trek.start_date else None
        db.session.commit()
        flash('Trek updated successfully.')
        return redirect(url_for('admin_treks'))

    available_staff = User.query.filter_by(role='staff', is_approved=True, is_blacklisted=False).all()
    return render_template('admin_trek_form.html', trek=trek, available_staff=available_staff)


@app.route('/admin/treks/delete/<int:trek_id>', methods=['POST'])
@login_required(role='admin')
def admin_delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.bookings:
        flash('Cannot delete this trek because it already has bookings.')
        return redirect(url_for('admin_treks'))
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully.')
    return redirect(url_for('admin_treks'))

@app.route('/admin/staff')
@login_required(role='admin')
def admin_staff():
    query = request.args.get('q', '')
    staff_query = User.query.filter_by(role='staff')
    if query:
        if query.isdigit():
            staff_query = staff_query.filter(User.id == int(query))
        else:
            staff_query = staff_query.filter(User.name.ilike(f'%{query}%'))
    staff_list = staff_query.all()
    return render_template('admin_staff.html', staff_list=staff_list, query=query)


@app.route('/admin/staff/approve/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def admin_approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.is_approved = True
    db.session.commit()
    flash(f'{staff.name} has been approved.')
    return redirect(url_for('admin_staff'))


@app.route('/admin/staff/blacklist/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def admin_blacklist_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.is_blacklisted = not staff.is_blacklisted
    db.session.commit()
    action = 'blacklisted' if staff.is_blacklisted else 'un-blacklisted'
    flash(f'{staff.name} has been {action}.')
    return redirect(url_for('admin_staff'))


@app.route('/admin/users')
@login_required(role='admin')
def admin_users():
    query = request.args.get('q', '')
    users_query = User.query.filter_by(role='trekker')
    if query:
        if query.isdigit():
            users_query = users_query.filter(User.id == int(query))
        else:
            users_query = users_query.filter(User.name.ilike(f'%{query}%'))
    users_list = users_query.all()
    return render_template('admin_users.html', users_list=users_list, query=query)


@app.route('/admin/users/blacklist/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def admin_blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()
    action = 'blacklisted' if user.is_blacklisted else 'un-blacklisted'
    flash(f'{user.name} has been {action}.')
    return redirect(url_for('admin_users'))

@app.route('/staff/dashboard')
@login_required(role='staff')
def staff_dashboard():
    staff_profile = StaffProfile.query.filter_by(user_id=session['user_id']).first()
    if not staff_profile:
        flash('Staff profile not found.')
        return redirect(url_for('logout'))
    assigned_treks = Trek.query.filter_by(staff_id=staff_profile.id).all()
    trek_data = []
    for trek in assigned_treks:
        booking_count = Booking.query.filter_by(trek_id=trek.id).count()
        trek_data.append({'trek': trek, 'booking_count': booking_count})
    return render_template('staff_dashboard.html', trek_data=trek_data)


@app.route('/staff/trek/<int:trek_id>', methods=['GET', 'POST'])
@login_required(role='staff')
def staff_manage_trek(trek_id):
    staff_profile = StaffProfile.query.filter_by(user_id=session['user_id']).first()
    trek = Trek.query.get_or_404(trek_id)

    # make sure this staff member is actually assigned to this trek
    if trek.staff_id != staff_profile.id:
        flash('You are not assigned to this trek.')
        return redirect(url_for('staff_dashboard'))

    if request.method == 'POST':
        new_status = request.form.get('status')
        new_slots = request.form.get('available_slots')

        # only allow staff-level status transitions
        allowed_statuses = ['Approved', 'Open', 'Closed', 'Completed']
        if new_status in allowed_statuses:
            trek.status = new_status

        if new_slots:
            new_slots = int(new_slots)
            # prevent setting available slots higher than total slots
            if new_slots <= trek.total_slots:
                trek.available_slots = new_slots
            else:
                flash('Available slots cannot exceed total slots.')
                return redirect(url_for('staff_manage_trek', trek_id=trek.id))

        db.session.commit()
        flash('Trek updated successfully.')
        return redirect(url_for('staff_manage_trek', trek_id=trek.id))

    participants = Booking.query.filter_by(trek_id=trek.id).all()
    return render_template('staff_manage_trek.html', trek=trek, participants=participants)

@app.route('/staff/profile', methods=['GET', 'POST'])
@login_required(role='staff')
def staff_profile_edit():
    user = User.query.get_or_404(session['user_id'])
    staff_profile = StaffProfile.query.filter_by(user_id=session['user_id']).first()

    if request.method == 'POST':
        user.name = request.form.get('name')
        staff_profile.phone_number = request.form.get('phone_number')
        staff_profile.experience_years = request.form.get('experience_years')
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('staff_dashboard'))

    return render_template('staff_profile.html', user=user, staff_profile=staff_profile)

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)