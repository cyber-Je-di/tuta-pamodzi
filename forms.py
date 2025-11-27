# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from wtforms import IntegerField
from wtforms.validators import NumberRange
from wtforms import TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length
# Keep the models import for validation methods, but the utility functions are now internal to the routes.
from models import User 

# Utility function to get the list of Tutors for the student registration form
# NOTE: The implementation of these functions should now be moved to the route file
# to ensure they run inside the app context.
def get_tutors():
    """Fetch a list of all tutors.

    Note:
        This function is deprecated in this file and should be used from
        `main_routes` to ensure it operates within the application context.

    Returns:
        list[tuple]: A list of tuples containing tutor IDs and names.
    """
    from models import User
    # This function is now redundant in forms.py but kept for reference
    return [(t.id, t.full_name) for t in User.query.filter_by(role='Tutor').all()]

def get_universities():
    """Fetch a list of all universities.

    Note:
        This function is deprecated in this file and should be used from
        `main_routes` to ensure it operates within the application context.

    Returns:
        list[tuple]: A list of tuples containing university IDs and names.
    """
    from models import University
    # This function is now redundant in forms.py but kept for reference
    return [(u.id, u.name) for u in University.query.all()]

## --- LOGIN FORM ---
class LoginForm(FlaskForm):
    """A form for user login.

    Fields:
        username (StringField): The user's username.
        password (PasswordField): The user's password.
        submit (SubmitField): The submit button.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

## --- STUDENT REGISTRATION FORM (The most complex role) ---
class StudentRegistrationForm(FlaskForm):
    """A form for student registration.

    This form includes fields for selecting a tutor and university, along
    with standard registration fields like name, username, email, and password.
    It also includes custom validators to ensure unique usernames and emails.
    """
    # CRITICAL FIX: Set choices to an empty list here, and dynamically populate it in the route
    tutor_id = SelectField('Select Your Tutor', coerce=int, validators=[DataRequired()], choices=[(0, 'Select a Tutor')])
    university_id = SelectField('Select Your University', coerce=int, validators=[DataRequired()], choices=[(0, 'Select a University')])
    
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register as Student')

    def validate_username(self, username):
        """Validate that the username is not already taken.

        Args:
            username (StringField): The username field from the form.

        Raises:
            ValidationError: If the username already exists in the database.
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        """Validate that the email address is not already registered.

        Args:
            email (StringField): The email field from the form.

        Raises:
            ValidationError: If the email already exists in the database.
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')
            
## --- TUTOR REGISTRATION FORM ---
# ... (TutorRegistrationForm remains the same)
class TutorRegistrationForm(FlaskForm):
    """A form for tutor registration.

    This form includes fields for a tutor's personal and login information,
    along with custom validators for unique usernames and emails.
    """
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register as Tutor')

    def validate_username(self, username):
        """Validate that the username is not already taken.

        Args:
            username (StringField): The username field from the form.

        Raises:
            ValidationError: If the username already exists in the database.
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        """Validate that the email address is not already registered.

        Args:
            email (StringField): The email field from the form.

        Raises:
            ValidationError: If the email already exists in the database.
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')
        

## --- ADMIN FORMS ---

class UniversityForm(FlaskForm):
    """A form for adding a new university."""
    name = StringField('University Name', validators=[DataRequired(), Length(max=100)])
    submit_uni = SubmitField('Add University')

class CategoryForm(FlaskForm):
    """A form for adding a new category to a university."""
    # This choice list will be dynamically populated in the route function
    university_id = SelectField('Select University', coerce=int, validators=[DataRequired()], choices=[(0, '--- Select University ---')])
    name = StringField('Category Name (e.g., School of Engineering)', validators=[DataRequired(), Length(max=100)])
    submit_cat = SubmitField('Add Category')

class CourseForm(FlaskForm):
    """A form for adding a new course to a category."""
    # This choice list will be dynamically populated in the route function
    category_id = SelectField('Select Category', coerce=int, validators=[DataRequired()], choices=[(0, '--- Select Category ---')])
    name = StringField('Course Name (e.g., Computer Science)', validators=[DataRequired(), Length(max=100)])
    code = StringField('Course Code (e.g., CSC3000)', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Add Course')

class SystemSettingForm(FlaskForm):
    """A form for updating system-wide settings."""
    # Field to edit the commission rate, displayed as a percentage (0-100)
    commission_rate = IntegerField('Commission Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100, message='Rate must be between 0 and 100.')])
    submit = SubmitField('Update Settings')
    
# Choices for the 1-5 rating fields
RATING_CHOICES = [
    (5, '5 - Excellent'), 
    (4, '4 - Good'), 
    (3, '3 - Fair'), 
    (2, '2 - Poor'), 
    (1, '1 - Very Poor')
]

## --- TUTOR REVIEW FORM (Req 1.5.15, 1.5.16) ---
class TutorReviewForm(FlaskForm):
    """A form for students to submit a review for their tutor."""
    # Hidden field to identify the tutor being reviewed
    tutor_id = HiddenField(validators=[DataRequired()]) 
    
    # Overall Rating (Req 1.5.15)
    rating = SelectField('Overall Tutor Rating (1-5)', choices=RATING_CHOICES, coerce=int, validators=[DataRequired()])
    
    # Questionnaire Element 1: Content Clarity (Req 1.5.16)
    content_clear_score = SelectField('Content Clarity Score (1-5)', choices=RATING_CHOICES, coerce=int, validators=[DataRequired()])
    
    # Questionnaire Element 2: Tutor Responsiveness (Req 1.5.16)
    tutor_responsive_score = SelectField('Tutor Responsiveness Score (1-5)', choices=RATING_CHOICES, coerce=int, validators=[DataRequired()])
    
    # Optional detailed text review
    review_text = TextAreaField('Detailed Review (Optional)', validators=[Length(max=500)])
    
    submit = SubmitField('Submit Review')