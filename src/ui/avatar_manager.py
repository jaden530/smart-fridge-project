# src/ui/avatar_manager.py

import json
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AvatarEmotion(Enum):
    """Avatar emotional states."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    THINKING = "thinking"
    CONCERNED = "concerned"
    SURPRISED = "surprised"
    GREETING = "greeting"


class AvatarAnimation(Enum):
    """Avatar animation states."""
    IDLE = "idle"
    TALKING = "talking"
    LISTENING = "listening"
    POINTING_LEFT = "pointing_left"
    POINTING_RIGHT = "pointing_right"
    NODDING = "nodding"
    SHAKING_HEAD = "shaking_head"
    WAVING = "waving"


@dataclass
class AvatarState:
    """Current state of the avatar."""
    emotion: AvatarEmotion
    animation: AvatarAnimation
    message: Optional[str] = None
    is_speaking: bool = False
    eye_position: tuple = (0, 0)  # For eye tracking


class AvatarManager:
    """
    Manages the animated avatar's state, emotions, and responses.
    """

    def __init__(self):
        self.current_state = AvatarState(
            emotion=AvatarEmotion.NEUTRAL,
            animation=AvatarAnimation.IDLE
        )
        self.personality_traits = {
            'friendliness': 0.9,
            'formality': 0.3,
            'humor': 0.7,
            'expressiveness': 0.8
        }

        # Greeting templates
        self.greetings = {
            'morning': [
                "Good morning, {name}! ☀️",
                "Rise and shine, {name}!",
                "Hey {name}, ready for a great day?"
            ],
            'afternoon': [
                "Good afternoon, {name}!",
                "Hey {name}, how's your day going?",
                "Afternoon, {name}! Looking for a snack?"
            ],
            'evening': [
                "Good evening, {name}!",
                "Hey {name}, welcome back!",
                "Evening, {name}! Dinner time?"
            ],
            'night': [
                "Hey {name}, midnight snack?",
                "Can't sleep, {name}?",
                "Late night visit, {name}?"
            ],
            'default': [
                "Hey {name}!",
                "Welcome back, {name}!",
                "Hi there, {name}!"
            ]
        }

        # Context-aware responses
        self.responses = {
            'item_added': [
                "Got it! Added {item} to your inventory.",
                "Nice! {item} looks fresh.",
                "Added {item}. I'll keep track of that for you!"
            ],
            'item_removed': [
                "Removed {item} from inventory.",
                "Enjoy your {item}!",
                "{item} removed. Should I suggest recipes with the rest?"
            ],
            'expiring_soon': [
                "Heads up! Your {item} expires in {days} days.",
                "⚠️ Don't forget about the {item} - use it soon!",
                "Quick reminder: {item} is expiring soon!"
            ],
            'recipe_suggestion': [
                "I found a great recipe: {recipe}!",
                "How about {recipe} for dinner?",
                "You could make {recipe} with what you have!"
            ],
            'low_confidence': [
                "I'm not quite sure what that is. Can you help me?",
                "Hmm, was that {item}?",
                "I think I see {item}, but I'm not certain."
            ],
            'thank_you': [
                "You're welcome!",
                "Happy to help!",
                "Anytime! That's what I'm here for."
            ],
            'nutrition_warning': [
                "Looks like you're getting close to your calorie goal.",
                "Great protein intake today!",
                "You're right on track with your nutrition goals!"
            ]
        }

        print("🤖 Avatar Manager initialized")

    def greet_user(self, user_name: str, time_of_day: str = 'default') -> Dict:
        """
        Generate a personalized greeting.

        Args:
            user_name: Name of the user
            time_of_day: 'morning', 'afternoon', 'evening', 'night', or 'default'

        Returns:
            Avatar state dict with greeting
        """
        greetings_list = self.greetings.get(time_of_day, self.greetings['default'])
        greeting = random.choice(greetings_list).format(name=user_name)

        self.current_state = AvatarState(
            emotion=AvatarEmotion.GREETING,
            animation=AvatarAnimation.WAVING,
            message=greeting,
            is_speaking=True
        )

        return self.get_state_dict()

    def respond_to_action(
        self,
        action_type: str,
        context: Dict
    ) -> Dict:
        """
        Generate contextual response to user actions.

        Args:
            action_type: Type of action ('item_added', 'item_removed', etc.)
            context: Additional context data

        Returns:
            Avatar state dict with response
        """
        if action_type not in self.responses:
            print(f"⚠️  Unknown action type: {action_type}")
            return self.get_state_dict()

        response_templates = self.responses[action_type]
        response = random.choice(response_templates).format(**context)

        # Set appropriate emotion based on action
        emotion_map = {
            'item_added': AvatarEmotion.HAPPY,
            'item_removed': AvatarEmotion.NEUTRAL,
            'expiring_soon': AvatarEmotion.CONCERNED,
            'recipe_suggestion': AvatarEmotion.EXCITED,
            'low_confidence': AvatarEmotion.THINKING,
            'thank_you': AvatarEmotion.HAPPY,
            'nutrition_warning': AvatarEmotion.NEUTRAL
        }

        self.current_state = AvatarState(
            emotion=emotion_map.get(action_type, AvatarEmotion.NEUTRAL),
            animation=AvatarAnimation.TALKING,
            message=response,
            is_speaking=True
        )

        return self.get_state_dict()

    def set_thinking(self, message: str = "Let me think...") -> Dict:
        """Set avatar to thinking state."""
        self.current_state = AvatarState(
            emotion=AvatarEmotion.THINKING,
            animation=AvatarAnimation.IDLE,
            message=message,
            is_speaking=False
        )
        return self.get_state_dict()

    def set_listening(self) -> Dict:
        """Set avatar to listening state."""
        self.current_state = AvatarState(
            emotion=AvatarEmotion.NEUTRAL,
            animation=AvatarAnimation.LISTENING,
            is_speaking=False
        )
        return self.get_state_dict()

    def point_at_inventory(self, direction: str = "right") -> Dict:
        """Make avatar point at inventory display."""
        animation = (
            AvatarAnimation.POINTING_RIGHT if direction == "right"
            else AvatarAnimation.POINTING_LEFT
        )

        self.current_state = AvatarState(
            emotion=AvatarEmotion.NEUTRAL,
            animation=animation,
            is_speaking=False
        )
        return self.get_state_dict()

    def confirm_action(self, confirmed: bool, message: str) -> Dict:
        """Show confirmation or rejection."""
        if confirmed:
            self.current_state = AvatarState(
                emotion=AvatarEmotion.HAPPY,
                animation=AvatarAnimation.NODDING,
                message=message,
                is_speaking=True
            )
        else:
            self.current_state = AvatarState(
                emotion=AvatarEmotion.NEUTRAL,
                animation=AvatarAnimation.SHAKING_HEAD,
                message=message,
                is_speaking=True
            )

        return self.get_state_dict()

    def track_eyes(self, x: int, y: int) -> Dict:
        """
        Update eye position to track user.

        Args:
            x: Horizontal position (-1 to 1, 0 = center)
            y: Vertical position (-1 to 1, 0 = center)

        Returns:
            Updated state
        """
        self.current_state.eye_position = (x, y)
        return self.get_state_dict()

    def speak(self, message: str, emotion: AvatarEmotion = AvatarEmotion.NEUTRAL) -> Dict:
        """
        Make avatar speak a message.

        Args:
            message: Text to speak
            emotion: Emotion to display

        Returns:
            Avatar state
        """
        self.current_state = AvatarState(
            emotion=emotion,
            animation=AvatarAnimation.TALKING,
            message=message,
            is_speaking=True
        )

        return self.get_state_dict()

    def idle(self) -> Dict:
        """Set avatar to idle state."""
        self.current_state = AvatarState(
            emotion=AvatarEmotion.NEUTRAL,
            animation=AvatarAnimation.IDLE,
            is_speaking=False
        )
        return self.get_state_dict()

    def get_state_dict(self) -> Dict:
        """Get current state as dictionary for JSON serialization."""
        return {
            'emotion': self.current_state.emotion.value,
            'animation': self.current_state.animation.value,
            'message': self.current_state.message,
            'is_speaking': self.current_state.is_speaking,
            'eye_position': self.current_state.eye_position
        }

    def update_personality(self, traits: Dict):
        """Update avatar personality traits."""
        self.personality_traits.update(traits)
        print(f"🤖 Updated personality: {self.personality_traits}")
