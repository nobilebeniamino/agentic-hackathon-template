"""
Agentic System Metrics Tracking
Persistent metrics collection for planner, executor, and memory components
"""
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AgenticMetrics:
    """
    Centralized metrics tracking for the agentic system
    Uses Django cache for persistence with fallback to in-memory storage
    """
    
    def __init__(self):
        self.cache_prefix = "agentic_metrics_"
        self.default_ttl = 24 * 60 * 60  # 24 hours
        
    def increment_counter(self, metric_name: str, amount: int = 1):
        """Increment a counter metric"""
        try:
            cache_key = f"{self.cache_prefix}{metric_name}"
            current = cache.get(cache_key, 0)
            new_value = current + amount
            cache.set(cache_key, new_value, self.default_ttl)
            return new_value
        except Exception as e:
            logger.warning(f"Failed to increment metric {metric_name}: {e}")
            return 0
    
    def set_metric(self, metric_name: str, value: Any):
        """Set a metric to a specific value"""
        try:
            cache_key = f"{self.cache_prefix}{metric_name}"
            cache.set(cache_key, value, self.default_ttl)
        except Exception as e:
            logger.warning(f"Failed to set metric {metric_name}: {e}")
    
    def get_metric(self, metric_name: str, default=0):
        """Get a metric value"""
        try:
            cache_key = f"{self.cache_prefix}{metric_name}"
            return cache.get(cache_key, default)
        except Exception as e:
            logger.warning(f"Failed to get metric {metric_name}: {e}")
            return default
    
    def record_plan_generation(self, plan: Dict, success: bool = True):
        """Record a plan generation event"""
        self.increment_counter("plans_generated")
        
        if success:
            self.increment_counter("plans_successful")
            
            # Assess plan completeness
            completeness_score = 0
            if plan.get('immediate_actions'):
                completeness_score += 1
            if plan.get('followup_actions'):
                completeness_score += 1
            if plan.get('resources_needed'):
                completeness_score += 1
            if plan.get('monitoring_tasks'):
                completeness_score += 1
            
            # Record completeness (scale of 0-4)
            self.set_metric("last_plan_completeness", completeness_score)
            
            # Update average completeness
            total_plans = self.get_metric("plans_generated", 1)
            current_avg = self.get_metric("avg_plan_completeness", 0)
            new_avg = ((current_avg * (total_plans - 1)) + completeness_score) / total_plans
            self.set_metric("avg_plan_completeness", round(new_avg, 2))
        else:
            self.increment_counter("plans_failed")
    
    def record_action_execution(self, action: Dict, success: bool = True):
        """Record an action execution event"""
        self.increment_counter("actions_executed")
        
        if success:
            self.increment_counter("actions_successful")
        else:
            self.increment_counter("actions_failed")
        
        # Record action type for analysis
        action_type = action.get('action', 'unknown')
        action_type_key = f"action_type_{action_type.replace(' ', '_').lower()}"
        self.increment_counter(action_type_key)
    
    def record_memory_operation(self, operation_type: str, success: bool = True):
        """Record a memory operation (store, retrieve, etc.)"""
        if operation_type == "store":
            self.increment_counter("patterns_stored")
        elif operation_type == "retrieve":
            self.increment_counter("context_hits")
        elif operation_type == "awareness":
            self.increment_counter("awareness_queries")
        
        if success:
            self.increment_counter(f"{operation_type}_successful")
        else:
            self.increment_counter(f"{operation_type}_failed")
    
    def get_planner_metrics(self) -> Dict[str, Any]:
        """Get planner-specific metrics"""
        plans_generated = self.get_metric("plans_generated", 0)
        plans_successful = self.get_metric("plans_successful", 0)
        plans_failed = self.get_metric("plans_failed", 0)
        avg_completeness = self.get_metric("avg_plan_completeness", 0)
        
        success_rate = 0
        if plans_generated > 0:
            success_rate = round((plans_successful / plans_generated) * 100, 1)
        
        # Convert completeness score (0-4) to percentage
        completeness_percentage = round((avg_completeness / 4) * 100, 1) if avg_completeness > 0 else 0
        
        return {
            "plans_generated": plans_generated,
            "success_rate": success_rate,
            "completeness": completeness_percentage,
            "failed_plans": plans_failed
        }
    
    def get_executor_metrics(self) -> Dict[str, Any]:
        """Get executor-specific metrics"""
        actions_executed = self.get_metric("actions_executed", 0)
        actions_successful = self.get_metric("actions_successful", 0)
        actions_failed = self.get_metric("actions_failed", 0)
        
        success_rate = 0
        if actions_executed > 0:
            success_rate = round((actions_successful / actions_executed) * 100, 1)
        
        return {
            "actions_executed": actions_executed,
            "success_rate": success_rate,
            "failed_actions": actions_failed
        }
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory-specific metrics"""
        return {
            "patterns_stored": self.get_metric("patterns_stored", 0),
            "context_hits": self.get_metric("context_hits", 0),
            "awareness_queries": self.get_metric("awareness_queries", 0)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics for dashboard"""
        return {
            "planner": self.get_planner_metrics(),
            "executor": self.get_executor_metrics(),
            "memory": self.get_memory_metrics(),
            "last_updated": timezone.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics (for testing or maintenance)"""
        metrics_to_reset = [
            "plans_generated", "plans_successful", "plans_failed",
            "actions_executed", "actions_successful", "actions_failed",
            "patterns_stored", "context_hits", "awareness_queries",
            "avg_plan_completeness", "last_plan_completeness"
        ]
        
        for metric in metrics_to_reset:
            cache_key = f"{self.cache_prefix}{metric}"
            cache.delete(cache_key)
        
        logger.info("Agentic metrics reset")

# Global metrics instance
agentic_metrics = AgenticMetrics()
