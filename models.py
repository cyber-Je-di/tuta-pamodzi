# models.py
from extensions import db # Assuming 'db' is defined in app.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Utility for role checks (Requirement 1.1)
ROLES = {
    'Admin': 'Admin',
    'Tutor': 'Tutor',
    'Student': 'Student'
}

# ----------------------------------------------------------------------
# 1. CORE CONFIGURATION
# ----------------------------------------------------------------------

class SystemSetting(db.Model):
    __tablename__ = 'SystemSettings'
    id = db.Column(db.Integer, primary_key=True)
    # Defines the Admin's commission rate (e.g., 0.10 for 10%) - Requirement 1.4.9
    commission_rate = db.Column(db.Float, nullable=False, default=0.10) 
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# ----------------------------------------------------------------------
# 2. USER MANAGEMENT
# ----------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'Admin', 'Tutor', or 'Student'
    
    # Relationships/Foreign Keys for Students
    tutor_id = db.Column(db.Integer, db.ForeignKey('Users.id')) # Student's assigned Tutor (Requirement 1.3.5)
    university_id = db.Column(db.Integer, db.ForeignKey('Universities.id')) # Student's university (Requirement 1.2.1)
    university = db.relationship('University', backref='students', lazy=True)
    
    # Gated Access Statuses (Requirement 1.3.6)
    is_approved = db.Column(db.Boolean, nullable=False, default=False) 
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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_content_authorized(self):
        """Checks if a student can access content (Two-Step Gating)"""
        if self.role == ROLES['Student']:
            # Access granted only if BOTH approved AND paid (Requirement 1.3.6)
            return self.is_approved and self.is_paid_current_month
        return True # Tutors/Admins always have access for their roles

# ----------------------------------------------------------------------
# 3. CONTENT HIERARCHY
# ----------------------------------------------------------------------

class University(db.Model, UserMixin):
    __tablename__ = 'Universities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    categories = db.relationship('Category', backref='university', lazy=True)

class Category(db.Model):
    __tablename__ = 'Categories'
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('Universities.id'), nullable=False)
    # ADDED THE MISSING 'name' COLUMN
    name = db.Column(db.String(80), nullable=False) 
    courses = db.relationship('Course', backref='category', lazy=True)
    __table_args__ = (db.UniqueConstraint('university_id', 'name'),) # Ensure unique category names per university

class Course(db.Model):
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

class Payment(db.Model):
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