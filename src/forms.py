from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, FloatField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, Optional, ValidationError
from wtforms.fields import EmailField
from decimal import Decimal

class UserPreferencesForm(FlaskForm):
    dietary_preference = StringField('Dietary Preference', validators=[Optional()])
    calorie_goal = IntegerField('Daily Calorie Goal', validators=[Optional()])
    protein_goal = IntegerField('Daily Protein Goal (g)', validators=[Optional()])
    carb_goal = IntegerField('Daily Carbohydrate Goal (g)', validators=[Optional()])
    fat_goal = IntegerField('Daily Fat Goal (g)', validators=[Optional()])
    submit = SubmitField('Save Preferences')

class CreateFamilyForm(FlaskForm):
    name = StringField('Family Name', validators=[DataRequired()])
    shopping_day = SelectField('Preferred Shopping Day', 
                             choices=[('', 'Select a day'),
                                    ('monday', 'Monday'),
                                    ('tuesday', 'Tuesday'),
                                    ('wednesday', 'Wednesday'),
                                    ('thursday', 'Thursday'),
                                    ('friday', 'Friday'),
                                    ('saturday', 'Saturday'),
                                    ('sunday', 'Sunday')],
                             validators=[Optional()])
    budget = StringField('Monthly Grocery Budget', validators=[Optional()])
    submit = SubmitField('Create Family')

    def validate_budget(self, field):
        if field.data:
            try:
                # Remove currency symbol and commas
                clean_value = field.data.replace('$', '').replace(',', '')
                # Convert to float
                float_value = float(clean_value)
                # Store the converted value
                self.budget_float = float_value
            except ValueError:
                raise ValidationError('Please enter a valid number')
            
    def get_budget(self):
        """Get the cleaned budget value as a float"""
        if hasattr(self, 'budget_float'):
            return self.budget_float
        return None

class InviteFamilyMemberForm(FlaskForm):
    """Form for inviting new family members"""
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    role = SelectField('Member Role',
                      choices=[('member', 'Family Member'),
                              ('child', 'Child'),
                              ('admin', 'Admin')],
                      validators=[DataRequired()])
    can_edit_inventory = BooleanField('Can Edit Inventory', default=True)
    can_edit_shopping_list = BooleanField('Can Edit Shopping List', default=True)
    can_invite_members = BooleanField('Can Invite New Members', default=False)
    submit = SubmitField('Send Invitation')

class UpdateFamilySettingsForm(FlaskForm):
    """Form for updating family settings"""
    name = StringField('Family Name', validators=[DataRequired()])
    shopping_day = SelectField('Preferred Shopping Day',
                             choices=[('', 'Select a day'), 
                                    ('monday', 'Monday'),
                                    ('tuesday', 'Tuesday'),
                                    ('wednesday', 'Wednesday'),
                                    ('thursday', 'Thursday'),
                                    ('friday', 'Friday'),
                                    ('saturday', 'Saturday'),
                                    ('sunday', 'Sunday')],
                             validators=[Optional()])
    budget = FloatField('Monthly Grocery Budget', validators=[Optional()])
    submit = SubmitField('Update Settings')

class UpdateMemberPermissionsForm(FlaskForm):
    """Form for updating family member permissions"""
    role = SelectField('Member Role',
                      choices=[('member', 'Family Member'),
                              ('child', 'Child'),
                              ('admin', 'Admin')],
                      validators=[DataRequired()])
    can_edit_inventory = BooleanField('Can Edit Inventory')
    can_edit_shopping_list = BooleanField('Can Edit Shopping List')
    can_invite_members = BooleanField('Can Invite New Members')
    submit = SubmitField('Update Permissions')