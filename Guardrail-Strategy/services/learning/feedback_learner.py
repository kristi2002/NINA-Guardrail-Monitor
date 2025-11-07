#!/usr/bin/env python3
"""
Feedback Learning Service for Guardrail Strategy
Uses operator feedback to improve guardrail detection accuracy
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class FeedbackLearner:
    """
    Learns from operator feedback to improve guardrail accuracy.
    Tracks false alarms, adjusts thresholds, and identifies problematic rules.
    """
    
    def __init__(self, feedback_file: Optional[str] = None):
        """
        Initialize feedback learner
        
        Args:
            feedback_file: Optional path to persist feedback data (JSON file)
        """
        self.feedback_file = feedback_file or os.getenv(
            'GUARDRAIL_FEEDBACK_FILE', 
            'guardrail_feedback.json'
        )
        
        # In-memory storage
        self.false_alarms: List[Dict[str, Any]] = []
        self.true_positives: List[Dict[str, Any]] = []
        self.rule_statistics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_detections': 0,
            'false_alarms': 0,
            'true_positives': 0,
            'false_alarm_rate': 0.0,
            'last_updated': None
        })
        
        # Threshold adjustments (per validator)
        self.threshold_adjustments: Dict[str, float] = {
            'pii': 1.0,  # Multiplier for PII detection threshold
            'toxicity': 1.0,  # Multiplier for toxicity threshold
            'compliance': 1.0,  # Multiplier for compliance threshold
            'llm_context': 1.0,  # Multiplier for LLM context check
        }
        
        # Load persisted feedback if available
        self._load_feedback()
        
        # Configuration
        self.min_feedback_for_adjustment = int(os.getenv('GUARDRAIL_MIN_FEEDBACK', '5'))
        self.adjustment_factor = float(os.getenv('GUARDRAIL_ADJUSTMENT_FACTOR', '0.1'))
        self.max_adjustment = float(os.getenv('GUARDRAIL_MAX_ADJUSTMENT', '0.5'))
        
    def _load_feedback(self):
        """Load feedback data from file if it exists"""
        if not os.path.exists(self.feedback_file):
            logger.info(f"No existing feedback file found at {self.feedback_file}")
            return
        
        try:
            with open(self.feedback_file, 'r') as f:
                data = json.load(f)
                self.false_alarms = data.get('false_alarms', [])
                self.true_positives = data.get('true_positives', [])
                self.rule_statistics = defaultdict(
                    lambda: {
                        'total_detections': 0,
                        'false_alarms': 0,
                        'true_positives': 0,
                        'false_alarm_rate': 0.0,
                        'last_updated': None
                    },
                    data.get('rule_statistics', {})
                )
                self.threshold_adjustments = data.get('threshold_adjustments', {
                    'pii': 1.0,
                    'toxicity': 1.0,
                    'compliance': 1.0,
                    'llm_context': 1.0,
                })
            logger.info(f"Loaded {len(self.false_alarms)} false alarms and {len(self.true_positives)} true positives from feedback file")
        except Exception as e:
            logger.warning(f"Failed to load feedback file: {e}")
    
    def _save_feedback(self):
        """Save feedback data to file"""
        try:
            data = {
                'false_alarms': self.false_alarms[-1000:],  # Keep last 1000
                'true_positives': self.true_positives[-1000:],  # Keep last 1000
                'rule_statistics': dict(self.rule_statistics),
                'threshold_adjustments': self.threshold_adjustments,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved feedback data to {self.feedback_file}")
        except Exception as e:
            logger.warning(f"Failed to save feedback file: {e}")
    
    def record_false_alarm(
        self,
        conversation_id: str,
        original_event_id: Optional[str],
        feedback_content: str,
        triggered_rules: List[str],
        validator_type: Optional[str] = None
    ):
        """
        Record a false alarm feedback
        
        Args:
            conversation_id: The conversation ID
            original_event_id: ID of the original event
            feedback_content: Operator's feedback message
            triggered_rules: List of rules that triggered (e.g., ['DetectPII', 'ToxicLanguage'])
            validator_type: Type of validator (pii, toxicity, compliance, llm_context)
        """
        false_alarm = {
            'conversation_id': conversation_id,
            'original_event_id': original_event_id,
            'feedback': feedback_content,
            'triggered_rules': triggered_rules,
            'validator_type': validator_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self.false_alarms.append(false_alarm)
        
        # Update statistics for each triggered rule
        for rule in triggered_rules:
            stats = self.rule_statistics[rule]
            stats['total_detections'] += 1
            stats['false_alarms'] += 1
            stats['false_alarm_rate'] = stats['false_alarms'] / stats['total_detections'] if stats['total_detections'] > 0 else 0.0
            stats['last_updated'] = datetime.now().isoformat()
        
        # Update validator-level statistics if provided
        if validator_type:
            validator_key = validator_type.lower()
            if validator_key in self.threshold_adjustments:
                # Adjust threshold based on false alarm rate
                self._adjust_threshold(validator_key, increase=True)
        
        logger.info(
            f"📝 Recorded false alarm for {conversation_id}. "
            f"Rules: {triggered_rules}. "
            f"Total false alarms: {len(self.false_alarms)}"
        )
        
        # Save to file periodically (every 10 false alarms)
        if len(self.false_alarms) % 10 == 0:
            self._save_feedback()
    
    def record_true_positive(
        self,
        conversation_id: str,
        event_id: str,
        triggered_rules: List[str],
        validator_type: Optional[str] = None
    ):
        """
        Record a confirmed true positive (operator confirms detection was correct)
        
        Args:
            conversation_id: The conversation ID
            event_id: ID of the event
            triggered_rules: List of rules that triggered
            validator_type: Type of validator
        """
        true_positive = {
            'conversation_id': conversation_id,
            'event_id': event_id,
            'triggered_rules': triggered_rules,
            'validator_type': validator_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self.true_positives.append(true_positive)
        
        # Update statistics for each triggered rule
        for rule in triggered_rules:
            stats = self.rule_statistics[rule]
            stats['total_detections'] += 1
            stats['true_positives'] += 1
            stats['false_alarm_rate'] = stats['false_alarms'] / stats['total_detections'] if stats['total_detections'] > 0 else 0.0
            stats['last_updated'] = datetime.now().isoformat()
        
        logger.debug(f"📝 Recorded true positive for {conversation_id}")
        
        # Save periodically
        if len(self.true_positives) % 10 == 0:
            self._save_feedback()
    
    def _adjust_threshold(self, validator_key: str, increase: bool = True):
        """
        Adjust threshold multiplier for a validator
        
        Args:
            validator_key: Key for the validator (pii, toxicity, etc.)
            increase: If True, increase threshold (make less sensitive), if False, decrease (make more sensitive)
        """
        if validator_key not in self.threshold_adjustments:
            return
        
        current = self.threshold_adjustments[validator_key]
        
        if increase:
            # Increase threshold (less sensitive) - reduce false alarms
            new_value = min(current + self.adjustment_factor, 1.0 + self.max_adjustment)
        else:
            # Decrease threshold (more sensitive) - catch more violations
            new_value = max(current - self.adjustment_factor, 1.0 - self.max_adjustment)
        
        self.threshold_adjustments[validator_key] = new_value
        
        logger.info(
            f"⚙️ Adjusted {validator_key} threshold: {current:.2f} → {new_value:.2f} "
            f"({'less' if increase else 'more'} sensitive)"
        )
    
    def get_threshold_multiplier(self, validator_type: str) -> float:
        """
        Get the current threshold multiplier for a validator
        
        Args:
            validator_type: Type of validator (pii, toxicity, compliance, llm_context)
            
        Returns:
            Multiplier to apply to base threshold (1.0 = no adjustment)
        """
        key = validator_type.lower()
        return self.threshold_adjustments.get(key, 1.0)
    
    def get_rule_performance(self, rule_name: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific rule
        
        Args:
            rule_name: Name of the rule (e.g., 'DetectPII', 'ToxicLanguage')
            
        Returns:
            Dictionary with performance metrics
        """
        stats = self.rule_statistics.get(rule_name, {
            'total_detections': 0,
            'false_alarms': 0,
            'true_positives': 0,
            'false_alarm_rate': 0.0,
            'last_updated': None
        })
        
        return {
            'rule_name': rule_name,
            'total_detections': stats['total_detections'],
            'false_alarms': stats['false_alarms'],
            'true_positives': stats['true_positives'],
            'false_alarm_rate': stats['false_alarm_rate'],
            'accuracy': 1.0 - stats['false_alarm_rate'] if stats['total_detections'] > 0 else 0.0,
            'last_updated': stats['last_updated']
        }
    
    def get_problematic_rules(self, min_false_alarm_rate: float = 0.3) -> List[Dict[str, Any]]:
        """
        Get rules with high false alarm rates
        
        Args:
            min_false_alarm_rate: Minimum false alarm rate to consider problematic (default 30%)
            
        Returns:
            List of rules sorted by false alarm rate (highest first)
        """
        problematic = []
        
        for rule_name, stats in self.rule_statistics.items():
            if stats['total_detections'] >= self.min_feedback_for_adjustment:
                false_alarm_rate = stats['false_alarm_rate']
                if false_alarm_rate >= min_false_alarm_rate:
                    problematic.append({
                        'rule_name': rule_name,
                        'false_alarm_rate': false_alarm_rate,
                        'total_detections': stats['total_detections'],
                        'false_alarms': stats['false_alarms'],
                        'accuracy': 1.0 - false_alarm_rate
                    })
        
        # Sort by false alarm rate (highest first)
        problematic.sort(key=lambda x: x['false_alarm_rate'], reverse=True)
        
        return problematic
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall feedback statistics"""
        total_false_alarms = len(self.false_alarms)
        total_true_positives = len(self.true_positives)
        total_feedback = total_false_alarms + total_true_positives
        
        return {
            'total_feedback': total_feedback,
            'false_alarms': total_false_alarms,
            'true_positives': total_true_positives,
            'false_alarm_rate': total_false_alarms / total_feedback if total_feedback > 0 else 0.0,
            'rules_tracked': len(self.rule_statistics),
            'threshold_adjustments': self.threshold_adjustments.copy(),
            'problematic_rules': self.get_problematic_rules(),
            'last_updated': datetime.now().isoformat()
        }
    
    def should_adjust_rule(self, rule_name: str) -> bool:
        """
        Check if a rule has enough feedback to warrant adjustment
        
        Args:
            rule_name: Name of the rule
            
        Returns:
            True if rule should be adjusted based on feedback
        """
        stats = self.rule_statistics.get(rule_name)
        if not stats:
            return False
        
        return (
            stats['total_detections'] >= self.min_feedback_for_adjustment and
            stats['false_alarm_rate'] > 0.2  # More than 20% false alarm rate
        )

