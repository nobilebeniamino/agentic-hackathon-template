"""
Agentic Emergency Response System
Main orchestrator that coordinates Planner, Executor, and Memory components
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from .planner import EmergencyPlanner
from .executor import EmergencyExecutor
from .memory import EmergencyMemory
from .responders import classify_message
from .disaster_feeds import get_disaster_feed

logger = logging.getLogger(__name__)

class AgenticEmergencySystem:
    """
    Main agentic system that orchestrates emergency response using:
    - Planner: Decomposes emergencies into actionable tasks
    - Executor: Carries out planned actions using available tools
    - Memory: Maintains context and learns from interactions
    """
    
    def __init__(self):
        self.planner = EmergencyPlanner()
        self.executor = EmergencyExecutor()
        self.memory = EmergencyMemory()
        self.system_name = "Agentic Emergency Response AI"
    
    def process_emergency(self, message: str, latitude: float, longitude: float, 
                         user_language: str = None, conversation_id: int = None, 
                         session_key: str = None) -> Dict[str, Any]:
        """
        Main entry point for processing emergency messages using agentic architecture
        
        Args:
            message: Emergency message from user
            latitude: User's latitude
            longitude: User's longitude
            user_language: User's preferred language
            conversation_id: ID of parent message if this is a follow-up
            session_key: User's session for conversation tracking
            
        Returns:
            Comprehensive emergency response with planning, execution, and memory integration
        """
        
        start_time = timezone.now()
        logger.info(f"Processing emergency with agentic system: {message[:50]}...")
        
        try:
            # Step 1: Check if this is a conversation follow-up
            conversation_context = self._get_conversation_context(conversation_id) if conversation_id else None
            
            # Step 2: Get contextual information
            context = self._gather_context(message, latitude, longitude, user_language, conversation_context)
            
            # Step 2: Initial classification using existing responder
            classification = classify_message(
                message, latitude, longitude, 
                context.get('disaster_feed', ''), 
                user_language
            )
            
            # Step 3: Enhance context with classification and memory
            enhanced_context = self._enhance_context_with_memory(context, classification)
            
            # Step 4: Plan comprehensive response (with conversation context)
            response_plan = self.planner.plan_response(
                message=message,
                location={'lat': latitude, 'lon': longitude},
                severity=classification.get('severity', 'UNKNOWN'),
                category=classification.get('category', 'UNKNOWN'),
                language=user_language or 'en',
                conversation_context=conversation_context
            )
            
            # Step 5: Execute the plan
            execution_log = self.executor.execute_plan(response_plan, enhanced_context)
            
            # Step 6: Store interaction in memory for future learning
            interaction_id = f"emergency_{int(start_time.timestamp())}"
            self.memory.store_interaction(
                message_id=hash(interaction_id),  # Simplified ID
                context=enhanced_context,
                plan=response_plan,
                execution_log=execution_log
            )
            
            # Step 7: Prepare comprehensive response
            agentic_response = self._prepare_agentic_response(
                classification, response_plan, execution_log, enhanced_context
            )
            
            end_time = timezone.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.info(f"Agentic emergency processing completed in {processing_time:.2f}s")
            
            return agentic_response
            
        except Exception as e:
            logger.error(f"Agentic system error: {str(e)}")
            # Fallback to basic classification
            return classify_message(message, latitude, longitude, "", user_language)
    
    def _gather_context(self, message: str, latitude: float, longitude: float, 
                       user_language: str, conversation_context: Dict = None) -> Dict[str, Any]:
        """Gather comprehensive context for emergency processing"""
        
        context = {
            'message': message,
            'location': {'lat': latitude, 'lon': longitude},
            'user_language': user_language,
            'timestamp': timezone.now().isoformat(),
            'system_version': '1.0-agentic'
        }
        
        # Add conversation context if this is a follow-up
        if conversation_context:
            context['conversation'] = conversation_context
            context['is_follow_up'] = True
            context['conversation_step'] = conversation_context.get('step', 1)
        else:
            context['is_follow_up'] = False
            context['conversation_step'] = 1
        
        # Get disaster feed context
        try:
            disaster_feed = get_disaster_feed(latitude, longitude)
            context['disaster_feed'] = disaster_feed
        except Exception as e:
            logger.warning(f"Could not fetch disaster feed: {str(e)}")
            context['disaster_feed'] = ""
        
        # Get situational awareness from memory
        try:
            situational_awareness = self.memory.get_situational_awareness(
                location={'lat': latitude, 'lon': longitude}
            )
            context['situational_awareness'] = situational_awareness
        except Exception as e:
            logger.warning(f"Could not get situational awareness: {str(e)}")
            context['situational_awareness'] = {}
        
        return context
    
    def _enhance_context_with_memory(self, context: Dict, classification: Dict) -> Dict:
        """Enhance context with relevant historical data from memory"""
        
        enhanced_context = context.copy()
        enhanced_context.update({
            'category': classification.get('category'),
            'severity': classification.get('severity'),
            'initial_instructions': classification.get('instructions', [])
        })
        
        # Get relevant historical context
        try:
            relevant_context = self.memory.get_relevant_context(
                location=context['location'],
                category=classification.get('category', 'UNKNOWN'),
                severity=classification.get('severity', 'UNKNOWN')
            )
            enhanced_context['historical_context'] = relevant_context
        except Exception as e:
            logger.warning(f"Could not get relevant context: {str(e)}")
            enhanced_context['historical_context'] = {}
        
        return enhanced_context
    
    def _prepare_agentic_response(self, classification: Dict, plan: Dict, 
                                execution_log: Dict, context: Dict) -> Dict[str, Any]:
        """Prepare comprehensive agentic response with conversation management"""
        
        # Start with basic classification
        response = classification.copy()
        
        # Handle conversation management from plan
        conversation_mgmt = plan.get('conversation_management', {})
        
        # Update classification if the conversation revealed new information
        if conversation_mgmt.get('severity_update'):
            response['severity'] = conversation_mgmt['severity_update']
        if conversation_mgmt.get('category_update'):
            response['category'] = conversation_mgmt['category_update']
        
        # Add agentic enhancements
        response.update({
            'agentic_system': {
                'enabled': True,
                'system_name': self.system_name,
                'processing_mode': 'full_agentic'
            },
            'comprehensive_plan': plan,
            'execution_log': execution_log,
            'contextual_awareness': {
                'disaster_feed_active': bool(context.get('disaster_feed')),
                'historical_incidents': len(context.get('historical_context', {}).get('similar_incidents', [])),
                'situational_factors': context.get('situational_awareness', {})
            },
            'enhanced_instructions': self._merge_instructions(
                classification.get('instructions', []),
                plan,
                execution_log
            ),
            'monitoring_recommendations': plan.get('monitoring_tasks', []),
            'resource_requirements': plan.get('resources_needed', []),
            'confidence_indicators': {
                'classification_confidence': 'high',
                'plan_completeness': self._assess_plan_completeness(plan),
                'execution_success': execution_log.get('final_status') == 'completed'
            },
            # Conversation management
            'conversation': {
                'needs_follow_up': conversation_mgmt.get('needs_follow_up', False),
                'follow_up_question': conversation_mgmt.get('follow_up_question', ''),
                'conversation_complete': conversation_mgmt.get('conversation_complete', True),
                'is_follow_up': context.get('is_follow_up', False),
                'step': context.get('conversation_step', 1),
                'reason_for_follow_up': conversation_mgmt.get('reason_for_follow_up', '')
            }
        })
        
        return response
    
    def _merge_instructions(self, basic_instructions: list, plan: Dict, 
                          execution_log: Dict) -> list:
        """Merge basic instructions with citizen-focused agentic plan insights"""
        
        enhanced_instructions = basic_instructions.copy()
        
        # Limit basic instructions to avoid overwhelming response
        if len(enhanced_instructions) > 3:
            enhanced_instructions = enhanced_instructions[:3]
        
        # Add high-priority citizen-focused actions from plan (max 2)
        immediate_actions = plan.get('immediate_actions', [])
        
        # Filter for citizen-appropriate actions and sort by priority
        citizen_actions = [
            action for action in immediate_actions 
            if self._is_citizen_appropriate_action(action.get('action', ''))
        ]
        priority_actions = sorted(citizen_actions, key=lambda x: x.get('priority', 0), reverse=True)[:2]
        
        for action in priority_actions:
            enhanced_instructions.append(f"🔥 Priority Action: {action.get('action')}")
        
        # Add successful execution insights (only meaningful ones)
        added_summaries = set()
        execution_count = 0
        for exec_result in execution_log.get('executed_actions', []):
            if execution_count >= 2:  # Limit to 2 system analyses max
                break
            if exec_result.get('status') == 'completed' and exec_result.get('result'):
                result = exec_result.get('result', {})
                summary = result.get('summary')
                # Only add meaningful summaries (not None or generic messages)
                if summary and summary not in added_summaries and self._is_meaningful_summary(summary):
                    enhanced_instructions.append(f"✅ System Analysis: {summary}")
                    added_summaries.add(summary)
                    execution_count += 1
        
        # Ensure total instructions don't exceed reasonable limit
        if len(enhanced_instructions) > 8:
            enhanced_instructions = enhanced_instructions[:8]
        
        return enhanced_instructions
    
    def _is_citizen_appropriate_action(self, action: str) -> bool:
        """Check if an action is appropriate for individual citizens"""
        
        # Convert to lowercase for checking
        action_lower = action.lower()
        
        # Actions that are NOT appropriate for citizens (institutional/professional)
        institutional_keywords = [
            'activate emergency protocols', 'issue public announcements', 
            'coordinate with authorities', 'deploy resources', 'notify agencies',
            'activate response plan', 'issue safety announcement', 'alert emergency services',
            'coordinate response', 'establish command', 'deploy personnel',
            'activate sirens', 'broadcast alerts', 'mobilize teams'
        ]
        
        # Check if action contains institutional keywords
        for keyword in institutional_keywords:
            if keyword in action_lower:
                return False
        
        # Actions that ARE appropriate for citizens
        citizen_keywords = [
            'call 112', 'call emergency', 'move to safety', 'seek shelter', 
            'evacuate', 'gather supplies', 'check on neighbors', 'stay updated',
            'listen to radio', 'follow instructions', 'prepare emergency kit',
            'stay calm', 'help others', 'document damage', 'avoid area',
            'take cover', 'drop and cover', 'exit building', 'find safe location'
        ]
        
        # Prefer actions with citizen keywords
        for keyword in citizen_keywords:
            if keyword in action_lower:
                return True
        
        # Default: allow if not clearly institutional
        return True
    
    def _assess_plan_completeness(self, plan: Dict) -> str:
        """Assess how complete the generated plan is"""
        
        completeness_score = 0
        max_score = 4
        
        if plan.get('immediate_actions'):
            completeness_score += 1
        if plan.get('followup_actions'):
            completeness_score += 1
        if plan.get('resources_needed'):
            completeness_score += 1
        if plan.get('monitoring_tasks'):
            completeness_score += 1
        
        if completeness_score >= 4:
            return 'comprehensive'
        elif completeness_score >= 3:
            return 'good'
        elif completeness_score >= 2:
            return 'adequate'
        else:
            return 'basic'
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and health"""
        
        return {
            'system_name': self.system_name,
            'components': {
                'planner': {'status': 'active', 'type': 'EmergencyPlanner'},
                'executor': {'status': 'active', 'type': 'EmergencyExecutor'},
                'memory': {'status': 'active', 'type': 'EmergencyMemory'}
            },
            'capabilities': [
                'emergency_classification',
                'response_planning',
                'action_execution',
                'contextual_memory',
                'situational_awareness',
                'multilingual_support',
                'disaster_feed_integration',
                'tool_orchestration'
            ],
            'version': '1.0-agentic',
            'architecture': 'planner_executor_memory'
        }
    
    def _is_meaningful_summary(self, summary: str) -> bool:
        """Check if a system analysis summary is meaningful to show to users"""
        
        if not summary or summary.strip() == '':
            return False
        
        # Filter out generic/technical messages that aren't useful for citizens
        generic_phrases = [
            'Action analyzed and executed',
            'Generated instruction steps',
            'Weather data would be fetched',
            'Found nearby emergency resources',
            'Simulated weather check',
            'Action analyzed with AI'
        ]
        
        summary_lower = summary.lower()
        for phrase in generic_phrases:
            if phrase.lower() in summary_lower:
                return False
        
        # Keep meaningful disaster-related summaries
        meaningful_keywords = [
            'disaster', 'active', 'detected', 'area', 'earthquake', 
            'flood', 'fire', 'emergency', 'alert', 'warning'
        ]
        
        for keyword in meaningful_keywords:
            if keyword.lower() in summary_lower:
                return True
        
        # Default: don't show unless clearly meaningful
        return False
    
    def _get_conversation_context(self, conversation_id: int) -> Dict[str, Any]:
        """Get context from previous conversation messages"""
        try:
            from .models import ReceivedMessage
            
            # Get the parent message and all follow-ups
            parent_message = ReceivedMessage.objects.get(id=conversation_id)
            follow_ups = parent_message.follow_ups.all().order_by('conversation_step')
            
            # Build conversation history
            all_messages = [parent_message] + list(follow_ups)
            previous_messages = []
            
            for msg in all_messages:
                previous_messages.append({
                    'step': msg.conversation_step,
                    'message': msg.user_message,
                    'category': msg.ai_category,
                    'severity': msg.ai_severity,
                    'timestamp': msg.received_at.isoformat()
                })
            
            return {
                'parent_id': parent_message.id,
                'step': len(all_messages) + 1,
                'previous_messages': previous_messages,
                'current_severity': parent_message.ai_severity,
                'current_category': parent_message.ai_category,
                'conversation_status': parent_message.conversation_status,
                'session_key': parent_message.session_key
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return None
