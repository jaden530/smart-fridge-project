# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Family(db.Model):
    """Family group model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shopping_day = db.Column(db.String(10))
    budget = db.Column(db.Float)
    dietary_restrictions = db.Column(db.JSON)

class FamilyMember(db.Model):
    """Association model between User and Family"""
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    can_edit_inventory = db.Column(db.Boolean, default=True)
    can_edit_shopping_list = db.Column(db.Boolean, default=True)
    can_invite_members = db.Column(db.Boolean, default=False)
    personal_dietary_restrictions = db.Column(db.JSON)

    # Relationships
    family = db.relationship('Family', backref='members')
    user = db.relationship('User', backref='memberships')

class FamilyInvitation(db.Model):
    """Model to handle family membership invitations"""
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invitee_email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')

    # Relationships
    family = db.relationship('Family', backref='invitations')
    inviter = db.relationship('User', backref='sent_invitations')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=True)  # Added email field
    dietary_preference = db.Column(db.String(64))
    calorie_goal = db.Column(db.Integer)
    protein_goal = db.Column(db.Integer)
    carb_goal = db.Column(db.Integer)
    fat_goal = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def families(self):
        """Get all families the user belongs to"""
        return [membership.family for membership in self.memberships]

    @property
    def primary_family(self):
        """Get the user's primary family (first joined or explicitly set)"""
        first_membership = self.memberships[0] if self.memberships else None
        return first_membership.family if first_membership else None

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    expiry_date = db.Column(db.DateTime)
    category = db.Column(db.String(64))
    nutritional_info = db.Column(db.JSON)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=True)

    user = db.relationship('User', backref='inventory_items')
    family = db.relationship('Family', backref='inventory_items')

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

    user = db.relationship('User', backref='nutrition_logs')

class HealthGoals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    calorie_goal = db.Column(db.Integer)
    protein_goal = db.Column(db.Integer)
    carb_goal = db.Column(db.Integer)
    fat_goal = db.Column(db.Integer)
    fiber_goal = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='health_goals')