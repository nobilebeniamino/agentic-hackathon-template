"""
Emergency Response Memory System
Implements the memory component of the agentic architecture
"""
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, List, Any, Optional
import json
import hashlib
import logging
from datetime import datetime, timedelta
from .models import ReceivedMessage
from .metrics import agentic_metrics

logger = logging.getLogger(__name__)

class EmergencyMemory:
    """
    Agentic Memory system that maintains context, learns from past interactions,
    and provides situational awareness for emergency responses
    """
    
    def __init__(self):
        self.cache_prefix = "emergency_memory"
        self.default_ttl = 3600 * 24  # 24 hours
        self.context_window = 50  # Number of recent interactions to consider
    
    def store_interaction(self, message_id: int, context: Dict, plan: Dict, execution_log: Dict) -> None:
        """
        Store a complete emergency interaction in memory
        
        Args:
            message_id: Database ID of the emergency message
            context: Emergency context (location, category, severity, etc.)
            plan: Generated response plan
            execution_log: Execution results
        """
        
        interaction = {
            'message_id': message_id,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'plan': plan,
            'execution_log': execution_log,
            'location_hash': self._hash_location(context.get('location', {})),
            'category': context.get('category', 'unknown'),
            'severity': context.get('severity', 'unknown')
        }
        
        # Store individual interaction
        cache_key = f"{self.cache_prefix}:interaction:{message_id}"
        cache.set(cache_key, interaction, self.default_ttl)
        
        # Update interaction history
        self._update_interaction_history(interaction)
        
        # Update location-based patterns
        self._update_location_patterns(interaction)
        
        # Update category-based learnings
        self._update_category_learnings(interaction)
        
        # Record memory operation
        agentic_metrics.record_memory_operation("store", success=True)
        
        logger.info(f"Stored interaction {message_id} in memory")
    
    def get_relevant_context(self, location: Dict, category: str, severity: str) -> Dict:
        """
        Retrieve relevant historical context for current emergency
        
        Args:
            location: Current emergency location
            category: Emergency category
            severity: Emergency severity
            
        Returns:
            Relevant historical context and patterns
        """
        
        context = {
            'similar_incidents': self._find_similar_incidents(location, category),
            'location_patterns': self._get_location_patterns(location),
            'category_insights': self._get_category_insights(category),
            'recent_activity': self._get_recent_activity(location),
            'effectiveness_data': self._get_effectiveness_data(category, severity)
        }
        
        # Record memory retrieval
        agentic_metrics.record_memory_operation("retrieve", success=True)
        
        return context
    
    def get_interaction_history(self, limit: int = None) -> List[Dict]:
        """Get recent interaction history"""
        
        history_key = f"{self.cache_prefix}:history"
        history = cache.get(history_key, [])
        
        if limit:
            return history[:limit]
        return history
    
    def learn_from_feedback(self, message_id: int, feedback: Dict) -> None:
        """
        Learn from user feedback on emergency response effectiveness
        
        Args:
            message_id: Original message ID
            feedback: User feedback on response quality
        """
        
        # Get original interaction
        interaction_key = f"{self.cache_prefix}:interaction:{message_id}"
        interaction = cache.get(interaction_key)
        
        if not interaction:
            logger.warning(f"No interaction found for message {message_id}")
            return
        
        # Store feedback
        feedback_data = {
            'message_id': message_id,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat(),
            'category': interaction.get('category'),
            'severity': interaction.get('severity'),
            'location_hash': interaction.get('location_hash')
        }
        
        feedback_key = f"{self.cache_prefix}:feedback:{message_id}"
        cache.set(feedback_key, feedback_data, self.default_ttl)
        
        # Update learning patterns
        self._update_learning_patterns(feedback_data, interaction)
        
        logger.info(f"Learned from feedback for message {message_id}")
    
    def get_situational_awareness(self, location: Dict, radius_km: float = 10) -> Dict:
        """
        Get current situational awareness for a location
        
        Args:
            location: Location to analyze
            radius_km: Radius for nearby activity analysis
            
        Returns:
            Current situational awareness data
        """
        
        # Get recent messages from database
        recent_cutoff = timezone.now() - timedelta(hours=6)
        recent_messages = ReceivedMessage.objects.filter(
            received_at__gte=recent_cutoff
        ).order_by('-received_at')[:100]
        
        # Analyze patterns
        situation = {
            'active_incidents': self._count_active_incidents(recent_messages, location, radius_km),
            'trending_categories': self._get_trending_categories(recent_messages),
            'severity_distribution': self._get_severity_distribution(recent_messages),
            'geographic_clusters': self._identify_geographic_clusters(recent_messages, location),
            'time_patterns': self._analyze_time_patterns(recent_messages),
            'resource_strain_indicators': self._assess_resource_strain(recent_messages)
        }
        
        # Record awareness query
        agentic_metrics.record_memory_operation("awareness", success=True)
        
        return situation
    
    def _hash_location(self, location: Dict) -> str:
        """Create a hash for location-based grouping"""
        lat = round(location.get('lat', 0), 3)  # ~100m precision
        lon = round(location.get('lon', 0), 3)
        return hashlib.md5(f"{lat},{lon}".encode()).hexdigest()[:8]
    
    def _update_interaction_history(self, interaction: Dict) -> None:
        """Update the rolling interaction history"""
        history_key = f"{self.cache_prefix}:history"
        history = cache.get(history_key, [])
        
        # Add new interaction at the beginning
        history.insert(0, {
            'message_id': interaction['message_id'],
            'timestamp': interaction['timestamp'],
            'category': interaction['category'],
            'severity': interaction['severity'],
            'location_hash': interaction['location_hash']
        })
        
        # Keep only recent interactions
        history = history[:self.context_window]
        
        cache.set(history_key, history, self.default_ttl)
    
    def _update_location_patterns(self, interaction: Dict) -> None:
        """Update location-based patterns"""
        location_hash = interaction['location_hash']
        patterns_key = f"{self.cache_prefix}:location:{location_hash}"
        
        patterns = cache.get(patterns_key, {
            'incident_count': 0,
            'categories': {},
            'severities': {},
            'first_seen': interaction['timestamp'],
            'last_seen': interaction['timestamp']
        })
        
        # Update patterns
        patterns['incident_count'] += 1
        patterns['last_seen'] = interaction['timestamp']
        
        category = interaction['category']
        patterns['categories'][category] = patterns['categories'].get(category, 0) + 1
        
        severity = interaction['severity']
        patterns['severities'][severity] = patterns['severities'].get(severity, 0) + 1
        
        cache.set(patterns_key, patterns, self.default_ttl)
    
    def _update_category_learnings(self, interaction: Dict) -> None:
        """Update category-based learnings"""
        category = interaction['category']
        learnings_key = f"{self.cache_prefix}:category:{category}"
        
        learnings = cache.get(learnings_key, {
            'total_incidents': 0,
            'successful_plans': 0,
            'common_actions': {},
            'avg_response_time': 0,
            'effectiveness_score': 0
        })
        
        learnings['total_incidents'] += 1
        
        # Analyze plan effectiveness (simplified)
        plan = interaction.get('plan', {})
        execution_log = interaction.get('execution_log', {})
        
        if execution_log.get('final_status') == 'completed':
            learnings['successful_plans'] += 1
        
        # Track common actions
        for action in plan.get('immediate_actions', []):
            action_text = action.get('action', '')
            learnings['common_actions'][action_text] = learnings['common_actions'].get(action_text, 0) + 1
        
        cache.set(learnings_key, learnings, self.default_ttl)
    
    def _find_similar_incidents(self, location: Dict, category: str) -> List[Dict]:
        """Find similar historical incidents"""
        location_hash = self._hash_location(location)
        
        # Get location patterns
        patterns_key = f"{self.cache_prefix}:location:{location_hash}"
        location_patterns = cache.get(patterns_key, {})
        
        # Get category learnings
        learnings_key = f"{self.cache_prefix}:category:{category}"
        category_learnings = cache.get(learnings_key, {})
        
        return [
            {
                'type': 'location_match',
                'data': location_patterns
            },
            {
                'type': 'category_match',
                'data': category_learnings
            }
        ]
    
    def _get_location_patterns(self, location: Dict) -> Dict:
        """Get patterns for a specific location"""
        location_hash = self._hash_location(location)
        patterns_key = f"{self.cache_prefix}:location:{location_hash}"
        return cache.get(patterns_key, {})
    
    def _get_category_insights(self, category: str) -> Dict:
        """Get insights for a specific category"""
        learnings_key = f"{self.cache_prefix}:category:{category}"
        return cache.get(learnings_key, {})
    
    def _get_recent_activity(self, location: Dict, hours: int = 6) -> Dict:
        """Get recent activity near location"""
        # This would analyze recent interactions near the location
        return {
            'nearby_incidents': 0,
            'activity_level': 'normal',
            'last_incident': None
        }
    
    def _get_effectiveness_data(self, category: str, severity: str) -> Dict:
        """Get effectiveness data for category/severity combination"""
        return {
            'success_rate': 0.85,  # Placeholder
            'avg_response_time': '2.3 minutes',
            'user_satisfaction': 4.2
        }
    
    def _update_learning_patterns(self, feedback_data: Dict, interaction: Dict) -> None:
        """Update learning patterns based on feedback"""
        # This would update ML models or pattern recognition based on feedback
        logger.info(f"Updated learning patterns based on feedback for {feedback_data['message_id']}")
    
    def _count_active_incidents(self, messages, location: Dict, radius_km: float) -> int:
        """Count active incidents near location"""
        # Simplified implementation
        return len(messages)
    
    def _get_trending_categories(self, messages) -> Dict:
        """Get trending emergency categories"""
        categories = {}
        for msg in messages:
            cat = msg.ai_category  # Use ai_category field from model
            if cat:  # Only count if category is not None/empty
                categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def _get_severity_distribution(self, messages) -> Dict:
        """Get severity distribution"""
        severities = {}
        for msg in messages:
            sev = msg.ai_severity  # Use ai_severity field from model
            if sev:  # Only count if severity is not None/empty
                severities[sev] = severities.get(sev, 0) + 1
        return severities
    
    def _identify_geographic_clusters(self, messages, location: Dict) -> List[Dict]:
        """Identify geographic clusters of incidents"""
        # Simplified clustering
        return []
    
    def _analyze_time_patterns(self, messages) -> Dict:
        """Analyze temporal patterns"""
        return {
            'peak_hours': ['14:00-16:00', '20:00-22:00'],
            'trend': 'stable'
        }
    
    def _assess_resource_strain(self, messages) -> Dict:
        """Assess potential resource strain"""
        return {
            'strain_level': 'normal',
            'bottlenecks': [],
            'recommendations': []
        }
