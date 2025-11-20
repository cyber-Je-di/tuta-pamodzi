# admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from sqlalchemy.orm import joinedload
# Make sure ALL models in the join chain are here:
from models import User, ROLES, University, Category, Course, SystemSetting 
from forms import UniversityForm, CategoryForm, CourseForm, SystemSettingForm

admin = Blueprint('admin', __name__, url_prefix='/admin')

# --- Custom Decorator for Admin Access Control ---
def admin_required(f):
    """Decorator to restrict access only to users with the 'Admin' role."""
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != ROLES['Admin']:
            flash('Access denied. You must be logged in as an Administrator.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function
# ------------------------------------------------

## --- 1. ADMIN DASHBOARD OVERVIEW ---
@admin.route('/dashboard')
@admin_required
def dashboard():
    # Fetch data summaries for the dashboard
    total_users = User.query.count()
    total_tutors = User.query.filter_by(role=ROLES['Tutor']).count()
    total_students = User.query.filter_by(role=ROLES['Student']).count()
    total_courses = Course.query.count()
    
    # Check current system settings
    system_setting = db.session.get(SystemSetting, 1)

    return render_template('admin_dashboard.html',
        total_users=total_users,
        total_tutors=total_tutors,
        total_students=total_students,
        total_courses=total_courses,
        commission_rate=system_setting.commission_rate if system_setting else 0.0
    )

## --- 2. UNIVERSITY & CATEGORY MANAGEMENT (Req 1.2.2) ---
@admin.route('/structure', methods=['GET', 'POST'])
@admin_required
def manage_structure():
    # Setup Forms
    uni_form = UniversityForm()
    cat_form = CategoryForm()
    
    # Populate choices for CategoryForm dynamically
    cat_form.university_id.choices = [(u.id, u.name) for u in University.query.all()]
    
    # Handle Form Submissions
    if uni_form.validate_on_submit() and uni_form.submit_uni.data:
        # Check for existence before adding
        if not University.query.filter_by(name=uni_form.name.data).first():
            new_uni = University(name=uni_form.name.data)
            db.session.add(new_uni)
            db.session.commit()
            flash(f'University "{new_uni.name}" added successfully.', 'success')
        else:
            flash(f'University "{uni_form.name.data}" already exists.', 'warning')
        return redirect(url_for('admin.manage_structure'))
        
    elif cat_form.validate_on_submit() and cat_form.submit_cat.data:
        # Check for existence before adding
        if not Category.query.filter_by(name=cat_form.name.data, university_id=cat_form.university_id.data).first():
            new_cat = Category(name=cat_form.name.data, university_id=cat_form.university_id.data)
            db.session.add(new_cat)
            db.session.commit()
            flash(f'Category "{new_cat.name}" added successfully.', 'success')
        else:
            flash(f'Category "{cat_form.name.data}" already exists for this University.', 'warning')
        return redirect(url_for('admin.manage_structure'))
        
    
    # CRITICAL FIX: Use class-bound attributes (University.categories and Category.courses)
    # instead of strings, as required by the ArgumentError.
    universities = University.query.options(
        joinedload(University.categories).joinedload(Category.courses)
    ).order_by(University.name).all()
    
    return render_template('admin_structure.html', 
        uni_form=uni_form, 
        cat_form=cat_form, 
        universities=universities
    )

## --- 3. COURSE MANAGEMENT (Req 1.2.3) ---
@admin.route('/courses', methods=['GET', 'POST'])
@admin_required
def manage_courses():
    course_form = CourseForm()
    
    # Populate choices dynamically
    # The choices for CourseForm are dependent on Category
    categories = Category.query.join(University).order_by(University.name, Category.name).all()
    # Create a list of tuples: (category_id, university_name + ' / ' + category_name)
    course_form.category_id.choices = [(c.id, f"{c.university.name} / {c.name}") for c in categories]

    if course_form.validate_on_submit():
        if not Course.query.filter_by(code=course_form.code.data, category_id=course_form.category_id.data).first():
            new_course = Course(
                name=course_form.name.data,
                code=course_form.code.data,
                category_id=course_form.category_id.data
            )
            db.session.add(new_course)
            db.session.commit()
            flash(f'Course "{new_course.code}: {new_course.name}" added successfully.', 'success')
        else:
            flash(f'Course code "{course_form.code.data}" already exists in this category.', 'warning')
        return redirect(url_for('admin.manage_courses'))

    # Fetch data for display
    courses = Course.query.join(Category).join(University).order_by(University.name, Category.name, Course.code).all()
    
    return render_template('admin_courses.html', 
        course_form=course_form, 
        courses=courses
    )

## --- 4. COMMISSION SETTINGS (Req 1.4.9) ---
@admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def manage_settings():
    setting = db.session.get(SystemSetting, 1)
    form = SystemSettingForm(obj=setting) # Populate form with current object data

    if form.validate_on_submit():
        # Update the commission rate
        setting.commission_rate = form.commission_rate.data / 100.0 # Convert percentage to decimal
        db.session.commit()
        flash(f'System commission rate updated to {form.commission_rate.data}%.', 'success')
        return redirect(url_for('admin.manage_settings'))

    # Display the rate as a percentage for the form field
    form.commission_rate.data = setting.commission_rate * 100
    
    return render_template('admin_settings.html', form=form)