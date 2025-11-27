# Tutoring Platform

This project is a web-based platform designed to connect students with tutors. It allows tutors to upload educational materials, manage their students, and track payments. Students can register, access content from their university, and review their tutors. An admin interface is also included for managing the platform's structure, such as universities, courses, and system settings.

## Features

- **User Roles:** Admin, Tutor, and Student roles with different permissions.
- **Content Management:** Tutors can upload documents for specific courses.
- **Student Management:** Tutors can approve students and record payments.
- **Tutor Reviews:** Students can review their tutors.
- **Admin Dashboard:** Admins can manage universities, categories, courses, and system settings.

## Project Structure

```
.
├── admin_routes.py         # Routes for admin functionality
├── app.py                  # Main application file
├── documents/              # Directory for uploaded documents
├── extensions.py           # Flask extension initializations
├── forms.py                # WTForms definitions
├── instance/               # Instance folder for SQLite database
├── main_routes.py          # Core application routes (login, registration, etc.)
├── models.py               # SQLAlchemy database models
├── requirements.txt        # Python dependencies
├── static/                 # Static files (CSS, JavaScript)
├── templates/              # Jinja2 templates
├── tutor_routes.py         # Routes for tutor functionality
└── utils.py                # Utility functions
```

## Setup and Installation

### Prerequisites

- Python 3.x
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/your-repository.git
   cd your-repository
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set the secret key:**
   - The application requires a secret key for session management. You can set it as an environment variable.
   ```bash
   export SECRET_KEY='your-secret-key'
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   The application will be available at `http://127.0.0.1:5000`.

## Usage

### Admin Access

- An admin user is created by default with the following credentials:
  - **Username:** `admin`
  - **Password:** `supersecurepassword123`
- The admin can log in to manage universities, courses, and system-wide settings like the commission rate.

### Tutor Registration

- Tutors can register through the "Register as Tutor" option on the registration page.
- Once registered, they can log in to their dashboard to manage students and upload content.

### Student Registration

- Students can register by selecting a tutor and university.
- After registration, their account needs to be approved by their selected tutor.
- Once approved and payment is recorded by the tutor, students gain access to the educational content.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
