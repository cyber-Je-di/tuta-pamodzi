# tutor_routes.py
import os
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app 
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from sqlalchemy import func # NEW: For aggregation (AVG, COUNT)
# NEW: Import TutorReview
from models import User, ROLES, Payment, Document, Course, SystemSetting, Category, University, TutorReview 

tutor = Blueprint('tutor', __name__, url_prefix='/tutor')

# --- Custom Decorator for Role Access Control (Requirement 1.1) ---
def tutor_required(f):
    """Decorator to restrict access only to users with the 'Tutor' role."""
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != ROLES['Tutor']:
            flash('Access denied. You must be logged in as a Tutor.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function
# ----------------------------------------------------------------

## --- 1. DASHBOARD OVERVIEW (Requirement 1.3.7, 1.5.17) ---
@tutor.route('/dashboard')
@tutor_required
def dashboard():
    # Fetch students assigned to the current tutor (Requirement 1.3.7)
    assigned_students = User.query.filter_by(tutor_id=current_user.id).order_by(User.full_name).all()
    
    # Calculate simple stats
    total_students = len(assigned_students)
    pending_approval = sum(1 for s in assigned_students if not s.is_approved)
    active_students = sum(1 for s in assigned_students if s.is_content_authorized())
    
    # Calculate revenue for the current month
    start_of_month = date.today().replace(day=1)
    monthly_revenue_query = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.tutor_id == current_user.id,
        Payment.payment_date >= start_of_month
    ).scalar()
    
    monthly_revenue = monthly_revenue_query or 0.0

    # --- Review Aggregation (Requirement 1.5.17) ---
    review_stats = db.session.query(
        func.count(TutorReview.id).label('total_reviews'),
        func.avg(TutorReview.rating).label('avg_rating'),
        func.avg(TutorReview.content_clear_score).label('avg_content_clear'),
        func.avg(TutorReview.tutor_responsive_score).label('avg_responsive')
    ).filter(TutorReview.tutor_id == current_user.id).one_or_none()

    # Fetch latest reviews
    latest_reviews = TutorReview.query.filter_by(
        tutor_id=current_user.id
    ).order_by(TutorReview.review_date.desc()).limit(5).all()
    # --- End Review Aggregation ---
    
    return render_template('tutor_dashboard.html', 
        students=assigned_students, 
        total_students=total_students,
        pending_approval=pending_approval,
        active_students=active_students,
        monthly_revenue=monthly_revenue,
        review_stats=review_stats, # NEW
        latest_reviews=latest_reviews # NEW
    )

## --- 2. STUDENT MANAGEMENT (Approval & Payment Recording) (Req 1.3.6, 1.3.8) ---

@tutor.route('/student/<int:student_id>/approve', methods=['POST'])
@tutor_required
def approve_student(student_id):
    student = db.session.get(User, student_id)
    
    # Security check: Ensure the tutor only manages their assigned students (Req 1.3.7)
    if not student or student.tutor_id != current_user.id or student.role != ROLES['Student']:
        flash('Student not found or unauthorized access.', 'danger')
        return redirect(url_for('tutor.dashboard'))
    
    # Change status from 'Pending' to 'Approved' (Req 1.3.6 - Status 1)
    student.is_approved = True
    db.session.commit()
    flash(f'{student.full_name} has been approved and is ready for payment.', 'success')
    return redirect(url_for('tutor.dashboard'))

@tutor.route('/student/<int:student_id>/record_payment', methods=['POST'])
@tutor_required
def record_payment(student_id):
    student = db.session.get(User, student_id)
    fee_amount = request.form.get('fee_amount', type=float)
    
    if not student or student.tutor_id != current_user.id or student.role != ROLES['Student']:
        flash('Student not found or unauthorized access.', 'danger')
        return redirect(url_for('tutor.dashboard'))

    if fee_amount is None or fee_amount <= 0:
        flash('Invalid fee amount entered.', 'danger')
        return redirect(url_for('tutor.dashboard'))
        
    # Get the current commission rate (Requirement 1.4.9)
    # Ensure SystemSetting ID 1 exists (Admin setup is required for this)
    system_setting = db.session.get(SystemSetting, 1)
    commission_rate = system_setting.commission_rate if system_setting else 0.0
    commission_amount = fee_amount * commission_rate
    
    # 1. Record the Payment (Requirement 1.3.8, 1.4.10)
    payment = Payment(
        student_id=student.id,
        tutor_id=current_user.id,
        amount=fee_amount,
        payment_date=date.today(),
        commission_amount=commission_amount
    )
    db.session.add(payment)
    
    # 2. Update Student Status (Requirement 1.3.6 - Status 2)
    student.is_paid_current_month = True
    
    db.session.commit()
    flash(f'Payment of ZMW{fee_amount:.2f} recorded for {student.full_name}. Access granted for the current month!', 'success')
    return redirect(url_for('tutor.dashboard'))


## --- 3. DOCUMENT UPLOAD (Requirement 1.2.3) ---
@tutor.route('/upload', methods=['GET', 'POST'])
@tutor_required
def upload_document():
    # Get the course structure for the dropdowns
    course_structure = Course.query.join(Category).join(University).order_by(University.name, Category.name, Course.name).all()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        title = request.form.get('title')
        course_id = request.form.get('course_id', type=int)

        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(request.url)
            
        # Basic file validation (only allowing PDF for simplicity)
        if not title or not course_id or course_id == 0 or not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            flash('Invalid form submission or file type. Must be PDF/DOC/DOCX.', 'danger')
            return redirect(request.url)

        # 1. Save the file securely
        filename = secure_filename(file.filename)
        # Use a path that includes the course ID to prevent collisions
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{course_id}_{current_user.id}_{filename}")
        file.save(file_path)
        
        # 2. Record metadata in the database
        document = Document(
            title=title,
            file_path=file_path,
            course_id=course_id,
            uploader_tutor_id=current_user.id
        )
        db.session.add(document)
        db.session.commit()
        
        flash(f'Document "{title}" uploaded successfully!', 'success')
        return redirect(url_for('tutor.upload_document'))

    return render_template('tutor_upload.html', course_structure=course_structure)