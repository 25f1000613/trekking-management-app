from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import db, User, StaffProfile
from werkzeug.security import generate_password_hash, check_password_hash

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


@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    return f"Welcome Admin {session.get('name')} (dashboard coming soon)"


@app.route('/staff/dashboard')
@login_required(role='staff')
def staff_dashboard():
    return f"Welcome Staff {session.get('name')} (dashboard coming soon)"


@app.route('/user/dashboard')
@login_required(role='trekker')
def user_dashboard():
    return f"Welcome {session.get('name')} (dashboard coming soon)"


with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)