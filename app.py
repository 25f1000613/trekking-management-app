from flask import Flask
from models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'change-this-later'

db.init_app(app)


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


with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)