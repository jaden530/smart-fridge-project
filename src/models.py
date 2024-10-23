from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()  # Don't pass `app` here, we will do it later in `main.py`

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    dietary_preference = db.Column(db.String(64))
    calorie_goal = db.Column(db.Integer)
    protein_goal = db.Column(db.Integer)
    carb_goal = db.Column(db.Integer)
    fat_goal = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    expiry_date = db.Column(db.DateTime)
    category = db.Column(db.String(64))
    nutritional_info = db.Column(db.JSON)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow)

    # Add these classes to models.py

class NutritionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    item_name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    fiber = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('nutrition_logs', lazy=True))

class HealthGoals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    calorie_goal = db.Column(db.Integer)
    protein_goal = db.Column(db.Integer)
    carb_goal = db.Column(db.Integer)
    fat_goal = db.Column(db.Integer)
    fiber_goal = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('health_goals', lazy=True, uselist=False))

    user = db.relationship('User', backref=db.backref('inventory_items', lazy=True))