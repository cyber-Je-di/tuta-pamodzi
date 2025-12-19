# lead_tutor_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, ROLES

lead_tutor = Blueprint('lead_tutor', __name__, url_prefix='/lead_tutor')

def lead_tutor_required(f):
    """Ensure a user is logged in and has the 'Lead Tutor' role."""
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != ROLES['Lead Tutor']:
            flash('Access denied. You must be a Lead Tutor.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@lead_tutor.route('/dashboard')
@lead_tutor_required
def dashboard():
    """Render the Lead Tutor's dashboard."""
    pending_tutors = User.query.filter_by(role=ROLES['Tutor'], tutor_status='pending').order_by(User.created_at).all()
    return render_template('lead_tutor_dashboard.html', pending_tutors=pending_tutors)

@lead_tutor.route('/tutor/<int:user_id>/approve', methods=['POST'])
@lead_tutor_required
def approve_tutor(user_id):
    """Approve a pending Tutor."""
    tutor = db.session.get(User, user_id)
    if tutor and tutor.role == ROLES['Tutor'] and tutor.tutor_status == 'pending':
        tutor.tutor_status = 'approved'
        db.session.commit()
        flash(f'Tutor {tutor.full_name} has been approved.', 'success')
    else:
        flash('Invalid request. Tutor not found or already processed.', 'danger')
    return redirect(url_for('lead_tutor.dashboard'))

@lead_tutor.route('/tutor/<int:user_id>/reject', methods=['POST'])
@lead_tutor_required
def reject_tutor(user_id):
    """Reject a pending Tutor."""
    tutor = db.session.get(User, user_id)
    if tutor and tutor.role == ROLES['Tutor'] and tutor.tutor_status == 'pending':
        tutor.tutor_status = 'rejected'
        db.session.commit()
        flash(f'Tutor {tutor.full_name} has been rejected.', 'warning')
    else:
        flash('Invalid request. Tutor not found or already processed.', 'danger')
    return redirect(url_for('lead_tutor.dashboard'))
