# main_routes.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
# ADDED TutorReviewForm import
from forms import LoginForm, StudentRegistrationForm, TutorRegistrationForm, TutorReviewForm
from extensions import db
# ADDED func import for aggregation queries
from sqlalchemy import func
from models import User, ROLES, Document, Course, Category, University, TutorReview

main = Blueprint('main', __name__)

# --- UTILITY FUNCTIONS (MOVED HERE TO ENSURE APP CONTEXT) ---
def get_tutors():
    """Fetch a list of all tutors for populating form select fields.

    Returns:
        list[tuple]: A list of tuples, where each tuple contains the ID and
                     full name of a tutor.
    """
    return [(t.id, t.full_name) for t in User.query.filter_by(role=ROLES['Tutor']).all()]

def get_universities():
    """Fetch a list of all universities for populating form select fields.

    Returns:
        list[tuple]: A list of tuples, where each tuple contains the ID and
                     name of a university.
    """
    return [(u.id, u.name) for u in University.query.all()]
# -------------------------------------------------------------

## --- LANDING PAGE ---
@main.route('/')
@main.route('/home')
def index():
    """Render the main landing page or redirect to the user's dashboard.

    If the user is authenticated, they are redirected to the appropriate
    dashboard based on their role (Admin, Tutor, or Student). Otherwise,
    the public landing page is rendered, showing a list of universities.

    Returns:
        werkzeug.wrappers.Response: A redirect response for authenticated
                                    users or a rendered template for
                                    anonymous users.
    """
    if current_user.is_authenticated:
        # Redirect based on role if logged in
        if current_user.role == ROLES['Admin']:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == ROLES['Lead Tutor']:
            return redirect(url_for('lead_tutor.dashboard'))
        elif current_user.role == ROLES['Tutor']:
            return redirect(url_for('tutor.dashboard'))
        else: # Student
            return redirect(url_for('main.student_dashboard'))
    
    universities = University.query.all()
    # Renders the main landing page with University selection (1.2.1)
    return render_template('landing.html', universities=universities)

## --- LOGIN ---
@main.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login.

    Displays the login form and processes user authentication. If the user
    is already authenticated, they are redirected to the main index page.
    On successful login, the user is redirected to their dashboard.

    Returns:
        werkzeug.wrappers.Response: A rendered template for the login page
                                    or a redirect response on successful
                                    authentication.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            # Log the user in and remember session
            login_user(user, remember=True)
            flash(f'Welcome back, {user.full_name}!', 'success')
            # Redirect to the user's dashboard after successful login
            return redirect(url_for('main.index'))
        else:
            flash('Login Failed. Check username and password.', 'danger')
            
    return render_template('login.html', form=form)

## --- REGISTRATION ---
@main.route('/register', methods=['GET', 'POST'])
def register_choice():
    """Display a page for users to choose their registration type.

    This route renders a simple page that allows a new user to select
    whether they want to register as a Student or a Tutor.

    Returns:
        str: The rendered HTML template for the registration choice page.
    """
    # Simple page to choose between Student and Tutor registration
    return render_template('register_choice.html')

@main.route('/register/student', methods=['GET', 'POST'])
def register_student():
    """Handle the registration process for new students.

    Displays the student registration form and processes the form submission.
    It populates the form's select fields with available tutors and
    universities. On successful registration, a new student user is created
    in the database, and they are redirected to the login page.

    Returns:
        werkzeug.wrappers.Response: The rendered template for the student
                                    registration page or a redirect to the
                                    login page upon success.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = StudentRegistrationForm()
    
    # CRITICAL FIX: Set the choices dynamically inside the route function
    tutor_choices = [(0, 'Select a Tutor')] + get_tutors()
    university_choices = [(0, 'Select a University')] + get_universities()
    
    form.tutor_id.choices = tutor_choices
    form.university_id.choices = university_choices
    
    if form.validate_on_submit():
        # Re-validate choices just in case of race condition or external change
        if form.tutor_id.data == 0 or form.university_id.data == 0:
            flash("Please select a valid Tutor and University.", 'danger')
            return render_template('register_student.html', form=form)
            
        new_student = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=ROLES['Student'],
            tutor_id=form.tutor_id.data,
            university_id=form.university_id.data,
        )
        new_student.set_password(form.password.data)
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Registration successful! Your account is pending Tutor approval and payment before you can access documents.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register_student.html', form=form)

@main.route('/register/tutor', methods=['GET', 'POST'])
def register_tutor():
    """Handle the registration process for new tutors.

    Displays the tutor registration form and processes the form submission.
    On successful registration, a new tutor user is created in the database,
    and they are redirected to the login page.

    Returns:
        werkzeug.wrappers.Response: The rendered template for the tutor
                                    registration page or a redirect to the
                                    login page upon success.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = TutorRegistrationForm()
    if form.validate_on_submit():
        new_tutor = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=ROLES['Tutor'],
            tutor_status='pending' # Tutors must be approved
        )
        new_tutor.set_password(form.password.data)
        
        db.session.add(new_tutor)
        db.session.commit()
        
        flash('Registration successful! Your account is now pending approval from a Lead Tutor.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register_tutor.html', form=form)

## --- LOGOUT ---
@main.route('/logout')
@login_required
def logout():
    """Log out the currently authenticated user.

    The user's session is cleared, and they are redirected to the main
    landing page.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the landing page.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

## --- DASHBOARD PLACEHOLDER (Student) ---
@main.route('/student/dashboard')
@login_required
def student_dashboard():
    """Render the student's dashboard.

    This page provides an overview for the student, including their current
    access status for viewing course content. Access is restricted to users
    with the 'Student' role.

    Returns:
        werkzeug.wrappers.Response: A rendered template for the student
                                    dashboard or a redirect if access is
                                    denied.
    """
    # Enforce student role access
    if current_user.role != ROLES['Student']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    # Check gated access status (Requirement 1.3.6)
    access_status = "Access Granted!" if current_user.is_content_authorized() else "Pending Tutor Approval/Payment."
    
    return render_template('student_dashboard.html', access_status=access_status)


@main.route('/student/content')
@login_required
def student_content():
    """Display educational content available to the student.

    This route checks if the student is authorized to view content (i.e.,
    approved by their tutor and has a current payment). If authorized, it
    fetches and displays all documents related to the courses at the
    student's university.

    Returns:
        werkzeug.wrappers.Response: A rendered template displaying the
                                    course materials, an access denied page,
                                    or a redirect if the user is not a
                                    student.
    """
    if current_user.role != ROLES['Student']:
        flash('Access denied. This page is only for students.', 'danger')
        return redirect(url_for('main.index'))

    # Check the student's access status (Requirement 1.3.6)
    if not current_user.is_content_authorized():
        # Status Gating: Student must be approved AND paid
        flash('Access denied. Please ensure your Tutor has approved your profile and recorded the monthly payment.', 'warning')
        return render_template('student_content_denied.html')

    # --- Content Fetching (Requirement 1.3.9) ---
    
    # 1. Get the list of Courses associated with the student's University
    # This ensures students only see documents relevant to their institution.
    if not current_user.university_id:
        documents = []
        flash('Your profile is not linked to a university. Please contact your Tutor.', 'danger')
    else:
        # Fetch all documents belonging to courses that are part of the student's university
        documents = Document.query.join(Document.course).join(Course.category).filter(
            Category.university_id == current_user.university_id
        ).order_by(Document.course_id, Document.upload_date.desc()).all()


    # Group documents by Course for easy display
    documents_by_course = {}
    for doc in documents:
        course_name_code = f"{doc.course.code}: {doc.course.name}"
        if course_name_code not in documents_by_course:
            documents_by_course[course_name_code] = []
        documents_by_course[course_name_code].append(doc)

    return render_template('student_content.html', documents_by_course=documents_by_course)


@main.route('/download/<int:document_id>')
@login_required
def download_document(document_id):
    """Provide a download link for a specific document.

    This route allows an authorized student to download a document file. It
    performs several security checks:
    1. Ensures the user is a student.
    2. Verifies the student is authorized to access content.
    3. Confirms the requested document belongs to the student's university.

    Args:
        document_id (int): The ID of the document to be downloaded.

    Returns:
        werkzeug.wrappers.Response: A file download response or a redirect
                                    if access is denied or the file is
                                    not found.
    """
    if current_user.role != ROLES['Student']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    document = db.session.get(Document, document_id)
    
    if not document:
        flash('Document not found.', 'danger')
        return redirect(url_for('main.student_content'))

    # Security Check 1: Content Gating (Requirement 1.3.6)
    if not current_user.is_content_authorized():
        flash('Authorization required to download content.', 'warning')
        return redirect(url_for('main.student_content'))
    
    # Security Check 2: Relevance Gating (Ensure document is from student's university)
    if document.course.category.university_id != current_user.university_id:
        flash('Access denied to content outside your assigned university.', 'danger')
        return redirect(url_for('main.student_content'))

    # Extract the directory and the actual filename for send_from_directory
    directory = current_app.config['UPLOAD_FOLDER']
    
    # Since the file_path includes the full path, we need to extract the filename 
    # based on how we saved it (e.g., /path/to/uploads/1_5_filename.pdf)
    
    # WARNING: This assumes the file_path is the full absolute path saved during upload.
    # We must ensure the file is served safely. The safest way is to use the full path 
    # to reconstruct the file's directory and name.
    
    file_dir = os.path.dirname(document.file_path)
    file_name = os.path.basename(document.file_path)

    try:
        # We use the base UPLOAD_FOLDER as the directory root for safety
        # and ensure the path is normalized.
        return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], 
                                   path=file_name, # path is relative to the directory
                                   as_attachment=True,
                                   # The saved file name is a composite one (courseid_tutorid_filename)
                                   # We must ensure file_name is what we expect based on the upload logic
                                   # Let's trust the logic in tutor_routes.py for now:
                                   download_name=file_name
                                  )
    except FileNotFoundError:
        flash('The file could not be found on the server.', 'danger')
        return redirect(url_for('main.student_content'))
    
@main.route('/review_tutor/<int:tutor_id>', methods=['GET', 'POST'])
@login_required
def review_tutor(tutor_id):
    """Handle the process for a student to review their tutor.

    This route displays a form for a student to submit a review for their
    assigned tutor. It includes checks to ensure that only the assigned
    student can submit a review and that they can only do so once.

    Args:
        tutor_id (int): The ID of the tutor being reviewed.

    Returns:
        werkzeug.wrappers.Response: The rendered template for the review
                                    form or a redirect upon successful
                                    submission or if access is denied.
    """
    # 1. Role Check
    if current_user.role != ROLES['Student']:
        flash('Access denied. Only students can review tutors.', 'danger')
        return redirect(url_for('main.index'))

    # 2. Authorization Check: Must be assigned to this tutor
    if current_user.tutor_id != tutor_id:
        flash('Access denied. You can only review your assigned tutor.', 'danger')
        return redirect(url_for('main.student_content'))
        
    tutor = db.session.get(User, tutor_id)
    if not tutor or tutor.role != ROLES['Tutor']:
        flash('Invalid tutor profile.', 'danger')
        return redirect(url_for('main.student_content'))

    # 3. Check if review already exists (UniqueConstraint)
    existing_review = TutorReview.query.filter_by(
        student_id=current_user.id, 
        tutor_id=tutor_id
    ).first()
    
    if existing_review:
        flash('You have already submitted a review for this tutor.', 'warning')
        return redirect(url_for('main.student_content'))
        
    form = TutorReviewForm(tutor_id=tutor_id)

    if form.validate_on_submit():
        new_review = TutorReview(
            tutor_id=tutor_id,
            student_id=current_user.id,
            rating=form.rating.data,
            review_text=form.review_text.data,
            content_clear_score=form.content_clear_score.data,
            tutor_responsive_score=form.tutor_responsive_score.data
        )
        db.session.add(new_review)
        db.session.commit()
        flash(f'Thank you! Your review for {tutor.full_name} has been submitted.', 'success')
        return redirect(url_for('main.student_content'))
        
    return render_template('review_tutor.html', form=form, tutor=tutor)

# main_routes.py (Append this new route)

@main.route('/tutors')
def list_tutors():
    """Display a public list of all tutors with aggregated review stats.

    This page is accessible to anyone and shows a ranked list of all tutors
    on the platform. Tutors are ranked by their average rating and the total
    number of reviews they have received.

    Returns:
        str: The rendered HTML template for the tutor list page.
    """
    # Fetch all Tutors and their aggregated review statistics in one query (Req 1.5.18)
    tutors_with_stats = db.session.query(
        User,
        func.avg(TutorReview.rating).label('avg_rating'),
        func.count(TutorReview.id).label('total_reviews')
    ).filter(
        User.role == ROLES['Tutor']
    ).outerjoin(
        TutorReview, User.id == TutorReview.tutor_id
    ).group_by(User.id).order_by(
        # Order by average rating descending, falling back to review count (Simple Ranking)
        func.avg(TutorReview.rating).desc(),
        func.count(TutorReview.id).desc()
    ).all()

    return render_template('tutor_list.html', tutors_with_stats=tutors_with_stats)

@main.route('/tutor/<int:tutor_id>')
def view_tutor_profile(tutor_id):
    """Display the public profile of a specific tutor.

    This page shows detailed information about a single tutor, including their
    name, aggregated review statistics, and a list of all reviews they have
    received.

    Args:
        tutor_id (int): The ID of the tutor whose profile is to be viewed.

    Returns:
        werkzeug.wrappers.Response: A rendered template of the tutor's
                                    profile or a redirect if the tutor is
                                    not found.
    """
    tutor = db.session.get(User, tutor_id)

    if not tutor or tutor.role != ROLES['Tutor']:
        flash('Tutor profile not found.', 'danger')
        return redirect(url_for('main.list_tutors'))

    # Fetch all detailed reviews for this tutor
    reviews = TutorReview.query.filter_by(
        tutor_id=tutor_id
    ).order_by(TutorReview.review_date.desc()).all()

    # Calculate aggregated stats for the single tutor (more detailed for the profile page)
    review_stats = db.session.query(
        func.count(TutorReview.id).label('total_reviews'),
        func.avg(TutorReview.rating).label('avg_rating'),
        func.avg(TutorReview.content_clear_score).label('avg_content_clear'),
        func.avg(TutorReview.tutor_responsive_score).label('avg_responsive')
    ).filter(TutorReview.tutor_id == tutor_id).one_or_none()
    
    # Students assigned to this tutor (for general profile stats)
    total_students = User.query.filter_by(tutor_id=tutor_id).count()

    return render_template('tutor_profile.html', 
        tutor=tutor, 
        reviews=reviews, 
        review_stats=review_stats,
        total_students=total_students
    )