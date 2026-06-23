# Trekking Management Application
A web application built with Flask, SQLite, and Bootstrap for managing trekking activities.

## Roles
- Admin: manages treks, staff, users, and bookings
- Trek Staff: manages assigned treks and participants
- User/Trekker: browses and books treks

## How to Run
1. Create and activate virtual environment:
   python -m venv venv
   venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Run the application:
   python app.py

4. Open browser at http://127.0.0.1:5000

## Admin Login
Email: admin@trek.com
Password: admin123

## Tech Stack
- Backend: Flask (Python)
- Database: SQLite via Flask-SQLAlchemy
- Frontend: Jinja2 templates, HTML, Bootstrap 5