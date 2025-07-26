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
    
    def plan_response(self, message: str, location: Dict[str, float], severity: str, category: str) -> List[Dict]:
        """
        Plan a comprehensive emergency response by breaking down into sub-tasks
        
        Args:
            message: User's emergency message
            location: Dict with 'lat' and 'lon' keys
            severity: Emergency severity level
            category: Emergency category
            
        Returns:
            List of planned tasks with priorities and actions
        """
        
        planning_prompt = f"""
You are an Emergency Response Planner Agent. Your role is to decompose emergency situations into actionable sub-tasks.

EMERGENCY DETAILS:
- Message: "{message}"
- Location: lat={location.get('lat', 0)}, lon={location.get('lon', 0)}
- Severity: {severity}
- Category: {category}

Create a comprehensive response plan as JSON with the following structure:
{{
    "immediate_actions": [
        {{"action": "...", "priority": 1-10, "estimated_time": "...", "responsible": "..."}}
    ],
    "followup_actions": [
        {{"action": "...", "priority": 1-10, "estimated_time": "...", "responsible": "..."}}
    ],
    "resources_needed": [
        {{"resource": "...", "quantity": "...", "urgency": "..."}}
    ],
    "monitoring_tasks": [
        {{"task": "...", "frequency": "...", "duration": "..."}}
    ]
}}

Prioritize life-safety first, then property protection, then recovery.
Consider local emergency services, weather conditions, and available resources.
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
