# models.py
from extensions import db # Assuming 'db' is defined in app.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Utility for role checks (Requirement 1.1)
ROLES = {
    'Admin': 'Admin',
    'Lead Tutor': 'Lead Tutor',
    'Tutor': 'Tutor',
    'Student': 'Student'
}

# ----------------------------------------------------------------------
# 1. CORE CONFIGURATION
# ----------------------------------------------------------------------

class SystemSetting(db.Model):
    """Represents system-wide settings for the application.

    This model stores configuration values that can be adjusted by an
    administrator, such as the commission rate for tutor payments.

    Attributes:
        id (int): The primary key for the setting.
        commission_rate (float): The percentage of tutor earnings that is
                                 taken as a commission.
        last_updated (datetime): The timestamp of the last update.
    """
    __tablename__ = 'SystemSettings'
    id = db.Column(db.Integer, primary_key=True)
    # Defines the Admin's commission rate (e.g., 0.10 for 10%) - Requirement 1.4.9
    commission_rate = db.Column(db.Float, nullable=False, default=0.10) 
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------------------------------------------
# 2. USER MANAGEMENT
# ----------------------------------------------------------------------

class User(UserMixin, db.Model):
    """Represents a user of the application.

    This model is used for all three user roles: Admin, Tutor, and Student.
    It includes authentication fields, personal information, and relationships
    to other models.

    Attributes:
        id (int): Primary key.
        username (str): The user's unique username.
        password_hash (str): The hashed password for the user.
        email (str): The user's unique email address.
        full_name (str): The user's full name.
        role (str): The user's role, one of 'Admin', 'Lead Tutor', 'Tutor', or 'Student'.
        tutor_status (str): The approval status for a tutor ('pending', 'approved', 'rejected').
        tutor_id (int): Foreign key linking a student to their tutor.
        university_id (int): Foreign key linking a student to their university.
        is_student_approved (bool): A flag indicating if a student is approved by a tutor.
        is_paid_current_month (bool): A flag indicating if a student has paid for the current month.
        created_at (datetime): The timestamp when the user was created.
    """
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'Admin', 'Lead Tutor', 'Tutor', or 'Student'
    tutor_status = db.Column(db.String(20), nullable=False, default='approved') # Tutors will be 'pending' on registration
    
    # Relationships/Foreign Keys for Students
    tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id')) # Student's assigned Tutor (Requirement 1.3.5)
    university_id = db.Column(db.Integer, db.ForeignKey('Universities.id')) # Student's university (Requirement 1.2.1)
    university = db.relationship('University', backref='students', lazy=True)
    
    # Gated Access Statuses for Students (Requirement 1.3.6)
    is_student_approved = db.Column(db.Boolean, nullable=False, default=False)
    is_paid_current_month = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships for other tables
    students_assigned = db.relationship('User', foreign_keys=[tutor_id], backref=db.backref('assigned_tutor', remote_side=[id]), lazy='dynamic')
    payments_made = db.relationship('Payment', foreign_keys='Payment.student_id', backref='student', lazy='dynamic')
    payments_received = db.relationship('Payment', foreign_keys='Payment.tutor_id', backref='tutor', lazy='dynamic')
    reviews_given = db.relationship('TutorReview', foreign_keys='TutorReview.student_id', backref='reviewer', lazy='dynamic')
    reviews_received = db.relationship('TutorReview', foreign_keys='TutorReview.tutor_id', backref='tutor_profile', lazy='dynamic')
    uploaded_documents = db.relationship('Document', backref='uploader_tutor', lazy='dynamic')
    
    
    def set_password(self, password):
        """Set the user's password to a hashed value.

        Args:
            password (str): The plaintext password to be hashed.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if a given password matches the user's hashed password.

        Args:
            password (str): The plaintext password to check.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        return check_password_hash(self.password_hash, password)
        
    def is_content_authorized(self):
        """Check if a user is authorized to access role-specific content.

        - Students: Access requires both tutor approval (`is_student_approved`) and
          a recorded payment for the current month (`is_paid_current_month`).
        - Tutors & Lead Tutors: Access requires their account to be approved
          (`tutor_status == 'approved'`).
        - Admins: Always have access.

        Returns:
            bool: True if the user is authorized, False otherwise.
        """
        if self.role == ROLES['Student']:
            # Access granted only if BOTH approved AND paid
            return self.is_student_approved and self.is_paid_current_month

        if self.role in [ROLES['Tutor'], ROLES['Lead Tutor']]:
            # Tutors must be approved to access their dashboards and content
            return self.tutor_status == 'approved'

        return True # Admins always have access

# ----------------------------------------------------------------------
# 3. CONTENT HIERARCHY
# ----------------------------------------------------------------------

class University(db.Model, UserMixin):
    """Represents an academic institution.

    Each university can have multiple categories of courses.

    Attributes:
        id (int): Primary key.
        name (str): The unique name of the university.
    """
    __tablename__ = 'Universities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    categories = db.relationship('Category', backref='university', lazy=True)

class Category(db.Model):
    """Represents a category of courses within a university.

    Examples include 'School of Engineering' or 'School of Humanities'.

    Attributes:
        id (int): Primary key.
        university_id (int): Foreign key linking to the parent university.
        name (str): The name of the category.
    """
    __tablename__ = 'Categories'
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('Universities.id'), nullable=False)
    # ADDED THE MISSING 'name' COLUMN
    name = db.Column(db.String(80), nullable=False) 
    courses = db.relationship('Course', backref='category', lazy=True)
    __table_args__ = (db.UniqueConstraint('university_id', 'name'),) # Ensure unique category names per university

class Course(db.Model):
    """Represents a single course within a category.

    Attributes:
        id (int): Primary key.
        category_id (int): Foreign key linking to the parent category.
        name (str): The name of the course (e.g., 'Introduction to Python').
        code (str): The unique code for the course (e.g., 'CS101').
    """
    __tablename__ = 'Courses'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('Categories.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False) # e.g., 'Maths'
    code = db.Column(db.String(20), nullable=False) # e.g., 'CSC3000' (Based on CourseForm)
    documents = db.relationship('Document', backref='course', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('category_id', 'name'),) # Ensure unique course names per category

# ----------------------------------------------------------------------
# 4. DOCUMENT MANAGEMENT
# ----------------------------------------------------------------------

class Document(db.Model):
    """Represents a document uploaded by a tutor for a specific course.

    Attributes:
        id (int): Primary key.
        title (str): The title of the document.
        file_path (str): The path to the document file on the server.
        course_id (int): Foreign key linking to the associated course.
        uploader_tutor_id (int): Foreign key linking to the tutor who uploaded it.
        upload_date (datetime): The timestamp of the upload.
    """
    __tablename__ = 'Documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Courses.id'), nullable=False)
    uploader_tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------------------------------------------
# 5. FINANCIAL TRACKING
# ----------------------------------------------------------------------

# class ProofOfPayment(db.Model):
#     """Represents an uploaded proof of payment from a student.
#
#     This model stores the image file uploaded by a student as proof of a
#     manual payment. Tutors can then review and approve these proofs to grant
#     course access.
#
#     Attributes:
#         id (int): Primary key.
#         student_id (int): Foreign key for the student uploading the proof.
#         tutor_id (int): Foreign key for the tutor who will receive the payment.
#         course_id (int): Foreign key for the course being paid for.
#         file_path (str): The path to the uploaded proof file.
#         status (str): The current status ('pending', 'approved', 'rejected').
#         upload_date (datetime): The timestamp of the upload.
#         reviewed_by_id (int): Foreign key for the user who reviewed the proof.
#         review_date (datetime): The timestamp of the review.
#     """
#     __tablename__ = 'ProofOfPayments'
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
#     tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
#     course_id = db.Column(db.Integer, db.ForeignKey('Courses.id'), nullable=False)
#     file_path = db.Column(db.String(255), unique=True, nullable=False)
#     status = db.Column(db.String(20), nullable=False, default='pending') # pending, approved, rejected
#     upload_date = db.Column(db.DateTime, default=datetime.utcnow)
#
#     # Tracking who reviewed the proof
#     reviewed_by_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
#     review_date = db.Column(db.DateTime)
#
#     # Relationships
#     student = db.relationship('User', foreign_keys=[student_id])
#     tutor = db.relationship('User', foreign_keys=[tutor_id])
#     course = db.relationship('Course', foreign_keys=[course_id])
#     reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class Payment(db.Model):
    """Represents a payment recorded by a tutor for a student.

    Attributes:
        id (int): Primary key.
        student_id (int): Foreign key for the student who made the payment.
        tutor_id (int): Foreign key for the tutor who received the payment.
        amount (float): The total amount of the payment.
        payment_date (date): The date the payment was made.
        commission_amount (float): The portion of the payment taken as commission.
    """
    __tablename__ = 'Payments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Amount the Tutor collected (Requirement 1.3.8)
    payment_date = db.Column(db.Date, nullable=False) 
    commission_amount = db.Column(db.Float) # Admin's portion (Requirement 1.4.10)

# ----------------------------------------------------------------------
# 6. TUTOR REVIEWS
# ----------------------------------------------------------------------

class TutorReview(db.Model):
    """Represents a review of a tutor submitted by a student.

    Attributes:
        id (int): Primary key.
        tutor_id (int): Foreign key for the tutor being reviewed.
        student_id (int): Foreign key for the student who wrote the review.
        rating (int): The overall rating from 1 to 5.
        review_text (str): The optional text of the review.
        content_clear_score (int): A 1-5 rating for content clarity.
        tutor_responsive_score (int): A 1-5 rating for tutor responsiveness.
        review_date (datetime): The timestamp when the review was submitted.
    """
    __tablename__ = 'TutorReviews'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5 (Requirement 1.5.15)
    review_text = db.Column(db.Text)
    content_clear_score = db.Column(db.Integer) # Questionnaire element (Requirement 1.5.16)
    tutor_responsive_score = db.Column(db.Integer) # Questionnaire element (Requirement 1.5.16)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('tutor_id', 'student_id'),)