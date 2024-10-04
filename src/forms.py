from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional

class UserPreferencesForm(FlaskForm):
    dietary_preference = StringField('Dietary Preference', validators=[Optional()])
    calorie_goal = IntegerField('Daily Calorie Goal', validators=[Optional()])
    protein_goal = IntegerField('Daily Protein Goal (g)', validators=[Optional()])
    carb_goal = IntegerField('Daily Carbohydrate Goal (g)', validators=[Optional()])
    fat_goal = IntegerField('Daily Fat Goal (g)', validators=[Optional()])
    submit = SubmitField('Save Preferences')