# src/core/family_manager.py

from datetime import datetime, timedelta
import secrets
from sqlalchemy.exc import SQLAlchemyError
from models import db, Family, FamilyMember, FamilyInvitation, User

class FamilyManager:
    def __init__(self):
        """Initialize the FamilyManager"""
        pass

    def create_family(self, name, creator, **kwargs):
        """
        Create a new family and add the creator as admin
        
        Args:
            name (str): Name of the family
            creator (User): User creating the family
            **kwargs: Additional family settings (shopping_day, budget, etc.)
        """
        try:
            family = Family(name=name, **kwargs)
            db.session.add(family)
            db.session.flush()  # Get the family ID without committing

            # Add creator as admin
            member = FamilyMember(
                family=family,
                user=creator,
                role='admin',
                can_edit_inventory=True,
                can_edit_shopping_list=True,
                can_invite_members=True
            )
            db.session.add(member)
            db.session.commit()
            return family
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def invite_member(self, family_id, inviter_id, invitee_email, role='member'):
        """
        Create an invitation for a new family member
        
        Args:
            family_id (int): ID of the family
            inviter_id (int): ID of the user sending the invitation
            invitee_email (str): Email of the person being invited
            role (str): Role to assign to the new member
        """
        try:
            # Generate unique token
            token = secrets.token_urlsafe(32)
            
            # Create invitation
            invitation = FamilyInvitation(
                family_id=family_id,
                inviter_id=inviter_id,
                invitee_email=invitee_email,
                token=token,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(invitation)
            db.session.commit()
            
            # Return token for email sending
            return token
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def process_invitation(self, token, accept=True):
        """
        Process a family invitation
        
        Args:
            token (str): Invitation token
            accept (bool): Whether to accept or reject the invitation
        """
        invitation = FamilyInvitation.query.filter_by(token=token).first()
        
        if not invitation or invitation.status != 'pending':
            return False, "Invalid or expired invitation"
            
        if datetime.utcnow() > invitation.expires_at:
            invitation.status = 'expired'
            db.session.commit()
            return False, "Invitation has expired"
            
        try:
            if accept:
                # Check if user exists
                user = User.query.filter_by(email=invitation.invitee_email).first()
                if not user:
                    return False, "User not found"
                    
                # Add user to family
                member = FamilyMember(
                    family_id=invitation.family_id,
                    user_id=user.id,
                    role='member',
                    can_edit_inventory=True,
                    can_edit_shopping_list=True,
                    can_invite_members=False
                )
                db.session.add(member)
                invitation.status = 'accepted'
            else:
                invitation.status = 'rejected'
                
            db.session.commit()
            return True, "Invitation processed successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def get_family_members(self, family_id):
        """Get all members of a family"""
        return FamilyMember.query.filter_by(family_id=family_id).all()

    def update_member_permissions(self, family_id, user_id, permissions):
        """
        Update a family member's permissions
        
        Args:
            family_id (int): ID of the family
            user_id (int): ID of the user
            permissions (dict): Dictionary of permissions to update
        """
        try:
            member = FamilyMember.query.filter_by(
                family_id=family_id,
                user_id=user_id
            ).first()
            
            if not member:
                return False, "Member not found"
                
            for key, value in permissions.items():
                if hasattr(member, key):
                    setattr(member, key, value)
                    
            db.session.commit()
            return True, "Permissions updated successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def remove_member(self, family_id, user_id):
        """Remove a member from a family"""
        try:
            member = FamilyMember.query.filter_by(
                family_id=family_id,
                user_id=user_id
            ).first()
            
            if not member:
                return False, "Member not found"
                
            db.session.delete(member)
            db.session.commit()
            return True, "Member removed successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def get_user_families(self, user_id):
        """Get all families a user belongs to"""
        return Family.query.join(FamilyMember).filter(
            FamilyMember.user_id == user_id
        ).all()

    def get_family_settings(self, family_id):
        """Get family settings"""
        return Family.query.get(family_id)

    def update_family_settings(self, family_id, settings):
        """Update family settings"""
        try:
            family = Family.query.get(family_id)
            if not family:
                return False, "Family not found"
                
            for key, value in settings.items():
                if hasattr(family, key):
                    setattr(family, key, value)
                    
            db.session.commit()
            return True, "Settings updated successfully"
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e