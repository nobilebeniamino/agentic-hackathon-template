"""
Emergency Response Planner
Implements the planning component of the agentic architecture
"""
import google.generativeai as genai
from django.conf import settings
from typing import List, Dict
import json
import logging
from .metrics import agentic_metrics

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class EmergencyPlanner:
    """
    Agentic Planner that decomposes emergency situations into actionable sub-tasks
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def plan_response(self, message: str, location: Dict[str, float], severity: str, category: str, language: str = "en", 
                     conversation_context: Dict = None) -> Dict:
        """
        Plan a comprehensive emergency response by breaking down into sub-tasks
        
        Args:
            message: User's emergency message
            location: Dict with 'lat' and 'lon' keys
            severity: Emergency severity level
            category: Emergency category
            language: User's preferred language (en/it)
            conversation_context: Previous conversation context if this is a follow-up
            
        Returns:
            Dict with planned tasks and conversation management
        """
        
        # Language instruction based on user preference
        language_instruction = ""
        if language == "it":
            language_instruction = "IMPORTANT: Respond in ITALIAN. All action descriptions and questions must be in Italian."
        else:
            language_instruction = "IMPORTANT: Respond in ENGLISH. All action descriptions and questions must be in English."
        
        # Conversation context
        conversation_prompt = ""
        if conversation_context:
            conversation_prompt = f"""
CONVERSATION CONTEXT:
- This is step {conversation_context.get('step', 1)} of an ongoing conversation
- Previous messages: {conversation_context.get('previous_messages', [])}
- Current severity: {conversation_context.get('current_severity', severity)}
- Current category: {conversation_context.get('current_category', category)}
"""
        
        planning_prompt = f"""
You are an Emergency Response Planner Agent. Your role is to create actionable emergency plans for INDIVIDUAL CITIZENS and manage emergency conversations.

{language_instruction}
{conversation_prompt}

EMERGENCY DETAILS:
- Message: "{message}"
- Location: lat={location.get('lat', 0)}, lon={location.get('lon', 0)}
- Severity: {severity}
- Category: {category}

Create a comprehensive response plan as JSON focused on INDIVIDUAL CITIZEN ACTIONS and CONVERSATION MANAGEMENT:

{{
    "immediate_actions": [
        {{"action": "...", "priority": 1-10, "estimated_time": "...", "responsible": "citizen"}}
    ],
    "followup_actions": [
        {{"action": "...", "priority": 1-10, "estimated_time": "...", "responsible": "citizen"}}
    ],
    "resources_needed": [
        {{"resource": "...", "quantity": "...", "urgency": "..."}}
    ],
    "monitoring_tasks": [
        {{"task": "...", "frequency": "...", "duration": "..."}}
    ],
    "conversation_management": {{
        "needs_follow_up": true/false,
        "follow_up_question": "...",
        "conversation_complete": true/false,
        "severity_update": "...",
        "category_update": "...",
        "reason_for_follow_up": "..."
    }}
}}

CONVERSATION MANAGEMENT GUIDELINES:
- Set "needs_follow_up" to true if you need more information to provide better help
- Ask follow-up questions to clarify:
  * Exact location details
  * Number of people involved
  * Severity of injuries/damage
  * Available resources/escape routes
  * Current safety status
- Update severity/category if new information changes the assessment
- Mark conversation complete when you have sufficient information for comprehensive help

RESPONSE GUIDELINES:
- Focus on actions an individual person can take (not emergency services or authorities)
- Prioritize personal safety and immediate protective actions
- Include practical steps like "call emergency services", "move to safety", "gather supplies"
- Avoid institutional actions like "issue public announcements" or "activate emergency protocols"
- Think from the perspective of someone asking "What should I do right now?"
- Include specific, actionable steps with clear timelines
- Consider available resources a typical citizen would have

Examples of GOOD actions:
- "Call 112 immediately to report the emergency"
- "Move to higher ground away from potential flooding"
- "Check on elderly neighbors and offer assistance"
- "Gather emergency supplies (water, first aid kit, flashlight)"
- "Stay updated via official emergency radio/TV broadcasts"

Examples of BAD actions (avoid these):
- "Activate emergency response protocols"
- "Issue public safety announcements"
- "Coordinate with civil protection agencies"
- "Deploy emergency resources"

Examples of GOOD follow-up questions:
- "Are you currently in a safe location?"
- "How many people are with you?"
- "Do you have access to emergency supplies?"
- "Can you describe the extent of the damage/situation?"
- "Are there any injuries that need immediate attention?"
"""

        try:
            response = self.model.generate_content(
                planning_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    candidate_count=1,
                )
            )
            
            raw_text = response.text
            
            # Extract JSON from markdown if present
            if "```json" in raw_text:
                start = raw_text.find("```json") + 7
                end = raw_text.find("```", start)
                if end != -1:
                    raw_text = raw_text[start:end].strip()
            
            plan = json.loads(raw_text)
            
            # Record successful plan generation
            agentic_metrics.record_plan_generation(plan, success=True)
            
            logger.info(f"Emergency plan generated for {category} at {location}")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            
            # Fallback plan
            fallback_plan = {
                "immediate_actions": [
                    {"action": "Contact emergency services", "priority": 10, "estimated_time": "immediate", "responsible": "user"}
                ],
                "followup_actions": [],
                "resources_needed": [
                    {"resource": "Emergency services", "quantity": "1", "urgency": "high"}
                ],
                "monitoring_tasks": [
                    {"task": "Monitor situation", "frequency": "continuous", "duration": "until resolved"}
                ]
            }
            
            # Record failed plan generation (but still return a fallback)
            agentic_metrics.record_plan_generation(fallback_plan, success=False)
            
            return fallback_plan
    
    def prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Sort tasks by priority and urgency"""
        return sorted(tasks, key=lambda x: x.get('priority', 5), reverse=True)
    
    def estimate_resource_requirements(self, plan: Dict) -> Dict:
        """Estimate total resource requirements from plan"""
        resources = {}
        
        for resource in plan.get('resources_needed', []):
            res_name = resource.get('resource', 'unknown')
            quantity = resource.get('quantity', '1')
            
            if res_name not in resources:
                resources[res_name] = {
                    'total_quantity': quantity,
                    'urgency_level': resource.get('urgency', 'medium')
                }
        
        return resources
