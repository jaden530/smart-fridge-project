# src/assistant/kitchen_assistant.py

from datetime import datetime
from typing import List, Dict, Optional

class KitchenAssistant:
    def __init__(self, inventory_manager, recipe_manager):
        self.inventory_manager = inventory_manager
        self.recipe_manager = recipe_manager
        self.current_context = {}
        self.conversation_history = []
        self.active_recipe = None
        self.teaching_mode = False
        
    def start_cooking_session(self, recipe_id: Optional[int] = None):
        """Start a new cooking session, optionally with a specific recipe"""
        self.current_context = {
            'session_start': datetime.now(),
            'current_step': 0,
            'active_tasks': [],
            'completed_tasks': [],
            'tips_given': set(),
            'safety_reminders': set(),
            'user_skill_observations': {}
        }
        
        if recipe_id:
            self.active_recipe = self.recipe_manager.get_recipe_details(recipe_id)
            self.current_context['recipe'] = self.active_recipe
            
    def process_message(self, message: str) -> Dict:
        """Process user message and generate appropriate response"""
        # Save message to history
        self.conversation_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now()
        })
        
        # Analyze message intent
        intent = self._analyze_intent(message)
        
        # Generate response based on intent and context
        response = self._generate_response(intent)
        
        # Save assistant's response
        self.conversation_history.append({
            'role': 'assistant',
            'content': response['message'],
            'timestamp': datetime.now()
        })
        
        return response
        
    def _analyze_intent(self, message: str) -> Dict:
        """Analyze user message to determine intent and extract relevant information"""
        intents = {
            'question': ['how', 'what', 'why', 'when', 'where', 'can you', 'could you'],
            'action': ['start', 'begin', 'let\'s', 'help', 'show', 'demonstrate'],
            'progress': ['next', 'done', 'finished', 'complete', 'ready'],
            'problem': ['help', 'stuck', 'problem', 'issue', 'wrong', 'mistake'],
            'technique': ['technique', 'method', 'way to', 'how to'],
            'safety': ['safe', 'careful', 'danger', 'warning', 'hot', 'sharp']
        }
        
        message_lower = message.lower()
        detected_intents = []
        
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
                
        # Determine primary and secondary intents
        primary_intent = detected_intents[0] if detected_intents else 'general'
        secondary_intents = detected_intents[1:] if len(detected_intents) > 1 else []
        
        return {
            'primary': primary_intent,
            'secondary': secondary_intents,
            'requires_demonstration': 'show' in message_lower or 'demonstrate' in message_lower,
            'technique_related': any(word in message_lower for word in ['technique', 'method', 'how to']),
            'safety_related': any(word in message_lower for word in ['safe', 'careful', 'danger', 'warning'])
        }
        
    def _generate_response(self, intent: Dict) -> Dict:
        """Generate appropriate response based on intent and current context"""
        response = {
            'message': '',
            'actions': [],
            'visual_cues': [],
            'safety_tips': [],
            'technique_tips': []
        }
        
        if self.active_recipe and intent['primary'] == 'progress':
            # Handle recipe progression
            next_step = self._get_next_recipe_step()
            if next_step:
                response['message'] = f"Let's move on to the next step: {next_step}"
                response['actions'] = self._get_step_actions(next_step)
                
        elif intent['technique_related']:
            # Handle technique demonstration requests
            technique_info = self._get_technique_guidance(intent)
            response.update(technique_info)
            
        elif intent['safety_related']:
            # Handle safety concerns
            safety_info = self._get_safety_guidance(intent)
            response.update(safety_info)
            
        elif intent['primary'] == 'question':
            # Handle questions
            answer = self._answer_question(intent)
            response.update(answer)
            
        # Add educational tips when appropriate
        if self.teaching_mode:
            tip = self._get_relevant_tip()
            if tip:
                response['message'] += f"\n\nCooking Tip: {tip}"
                
        return response
        
    def _get_next_recipe_step(self) -> Optional[str]:
        """Get the next step in the active recipe"""
        if not self.active_recipe:
            return None
            
        current_step = self.current_context['current_step']
        if current_step < len(self.active_recipe['instructions']):
            self.current_context['current_step'] += 1
            return self.active_recipe['instructions'][current_step]
        return None
        
    def _get_step_actions(self, step: str) -> List[Dict]:
        """Get the required actions for the current step"""
        # This will be expanded when we add visual demonstrations
        return [{'type': 'instruction', 'content': step}]
        
    def _get_technique_guidance(self, intent: Dict) -> Dict:
        """Get guidance for cooking techniques"""
        # This will be expanded with specific technique demonstrations
        return {
            'message': 'Let me show you the proper technique...',
            'technique_tips': ['Basic technique tip placeholder'],
            'visual_cues': ['technique_demonstration_placeholder']
        }
        
    def _get_safety_guidance(self, intent: Dict) -> Dict:
        """Get safety guidance"""
        return {
            'message': 'Safety is important! Here\'s what you need to know...',
            'safety_tips': ['Basic safety tip placeholder'],
            'visual_cues': ['safety_demonstration_placeholder']
        }
        
    def _answer_question(self, intent: Dict) -> Dict:
        """Generate an answer to a user's question"""
        return {
            'message': 'Here\'s what you need to know...',
            'actions': [],
            'visual_cues': []
        }
        
    def _get_relevant_tip(self) -> Optional[str]:
        """Get a relevant cooking tip based on current context"""
        # Will be expanded with more sophisticated tip selection
        return None

    def toggle_teaching_mode(self, enabled: bool = True):
        """Toggle teaching mode on/off"""
        self.teaching_mode = enabled
        if enabled:
            self.current_context['teaching_mode_start'] = datetime.now()