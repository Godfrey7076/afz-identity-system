# Air Force Zimbabwe Identity Verification System

A real-time identity verification system with facial recognition for the Air Force Zimbabwe Passes and Permits Unit.

## Features

- Real-time face verification using webcam
- Security number authentication
- Visitor management system
- Role-based access control (Pass Desk, Supervisor, Commander)
- Real-time notifications
- Air Force Zimbabwe blue theme with watermark

## Technology Stack

- **Backend**: Django + Django REST Framework
- **Frontend**: HTML, CSS, JavaScript
- **Face Recognition**: face-recognition library (dlib)
- **Real-time**: Django Channels
- **Database**: SQLite (development)

## Installation

1. Clone the repository:
\\\ash
git clone https://github.com/yourusername/afz-identity-system.git
cd afz-identity-system
\\\

2. Create virtual environment:
\\\ash
python -m venv venv
venv\Scripts\activate  # Windows
\\\

3. Install dependencies:
\\\ash
pip install -r requirements.txt
\\\

4. Run migrations:
\\\ash
python manage.py makemigrations
python manage.py migrate
\\\

5. Create superuser:
\\\ash
python manage.py createsuperuser
\\\

6. Run development server:
\\\ash
python manage.py runserver
\\\

## Project Structure

\\\
afz_identity_system/
├── afz_core/                 # Django project settings
├── identity_verification/    # Face verification app
├── users/                    # User management app
├── notifications/            # Notifications app
├── security/                 # Security app
├── templates/               # HTML templates
├── static/                  # Static files (CSS, JS, images)
├── media/                   # Media files
└── manage.py
\\\

## Usage

1. Access the system at \http://localhost:8000/\
2. Use security number + face verification for login
3. Manage visitors through the dashboard
4. Different views for Pass Desk, Supervisor, and Commander roles

## License

MIT License
