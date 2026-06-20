from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', or 'trekker'
    is_approved = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone_number = db.Column(db.String(15))
    experience_years = db.Column(db.Integer, default=0)

    treks = db.relationship('Trek', backref='assigned_staff', lazy=True)

    def __repr__(self):
        return f'<StaffProfile user_id={self.user_id}>'


class Trek(db.Model):
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff_profiles.id'), nullable=True)

    bookings = db.relationship('Booking', backref='trek', lazy=True)

    def __repr__(self):
        return f'<Trek {self.name}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')

    def __repr__(self):
        return f'<Booking user={self.user_id} trek={self.trek_id}>'