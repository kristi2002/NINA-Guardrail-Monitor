#!/usr/bin/env python3
"""
Operator Action Repository
Handles operator action-specific database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from models.operator_action import OperatorAction
import logging

logger = logging.getLogger(__name__)

class OperatorActionRepository(BaseRepository):
    """Repository for OperatorAction model with action-specific operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, OperatorAction)
    
    def get_by_action_id(self, action_id: str) -> Optional[OperatorAction]:
        """Get action by action_id"""
        return self.get_by_field('action_id', action_id)
    
    def get_by_conversation_id(self, conversation_id: str, limit: int = 100) -> List[OperatorAction]:
        """Get actions by conversation ID"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.conversation_id == conversation_id,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.action_timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting actions for conversation {conversation_id}: {e}")
            raise
    
    def get_by_operator_id(self, operator_id: str, limit: int = 100) -> List[OperatorAction]:
        """Get actions by operator ID"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.operator_id == operator_id,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.action_timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting actions for operator {operator_id}: {e}")
            raise
    
    def get_by_action_type(self, action_type: str, limit: int = 100) -> List[OperatorAction]:
        """Get actions by action type"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.action_type == action_type,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.action_timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting actions by type {action_type}: {e}")
            raise
    
    def get_by_status(self, status: str, limit: int = 100) -> List[OperatorAction]:
        """Get actions by status"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.status == status,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting actions by status {status}: {e}")
            raise
    
    def get_pending_actions(self, limit: int = 100) -> List[OperatorAction]:
        """Get pending actions"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.status == 'pending',
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting pending actions: {e}")
            raise
    
    def get_urgent_actions(self, limit: int = 100) -> List[OperatorAction]:
        """Get urgent actions"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.priority == 'urgent',
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting urgent actions: {e}")
            raise
    
    def get_actions_needing_followup(self, limit: int = 100) -> List[OperatorAction]:
        """Get actions needing follow-up"""
        try:
            return self.db.query(OperatorAction).filter(
                OperatorAction.requires_followup == True,
                OperatorAction.followup_completed == False,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting actions needing follow-up: {e}")
            raise
    
    def get_recent_actions(self, hours: int = 24, limit: int = 100) -> List[OperatorAction]:
        """Get recent actions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(OperatorAction).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).order_by(desc(OperatorAction.action_timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent actions: {e}")
            raise
    
    def complete_action(self, action_id: str, result: str = 'success', notes: str = None) -> Optional[OperatorAction]:
        """Complete an action"""
        try:
            action = self.get_by_action_id(action_id)
            if not action:
                return None
            
            action.complete_action(result, notes)
            self.db.commit()
            self.db.refresh(action)
            
            logger.info(f"Action {action_id} completed with result: {result}")
            return action
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing action {action_id}: {e}")
            raise
    
    def fail_action(self, action_id: str, reason: str = None) -> Optional[OperatorAction]:
        """Fail an action"""
        try:
            action = self.get_by_action_id(action_id)
            if not action:
                return None
            
            action.fail_action(reason)
            self.db.commit()
            self.db.refresh(action)
            
            logger.info(f"Action {action_id} failed: {reason}")
            return action
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error failing action {action_id}: {e}")
            raise
    
    def cancel_action(self, action_id: str, reason: str = None) -> Optional[OperatorAction]:
        """Cancel an action"""
        try:
            action = self.get_by_action_id(action_id)
            if not action:
                return None
            
            action.cancel_action(reason)
            self.db.commit()
            self.db.refresh(action)
            
            logger.info(f"Action {action_id} cancelled: {reason}")
            return action
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling action {action_id}: {e}")
            raise
    
    def complete_followup(self, action_id: str, notes: str = None) -> Optional[OperatorAction]:
        """Complete follow-up for an action"""
        try:
            action = self.get_by_action_id(action_id)
            if not action:
                return None
            
            action.complete_followup(notes)
            self.db.commit()
            self.db.refresh(action)
            
            logger.info(f"Follow-up completed for action {action_id}")
            return action
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing follow-up for action {action_id}: {e}")
            raise
    
    def get_action_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get action statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Total actions
            total_actions = self.db.query(OperatorAction).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).count()
            
            # Actions by type
            type_stats = self.db.query(
                OperatorAction.action_type,
                func.count(OperatorAction.id).label('count')
            ).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).group_by(OperatorAction.action_type).all()
            
            # Actions by status
            status_stats = self.db.query(
                OperatorAction.status,
                func.count(OperatorAction.id).label('count')
            ).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).group_by(OperatorAction.status).all()
            
            # Actions by priority
            priority_stats = self.db.query(
                OperatorAction.priority,
                func.count(OperatorAction.id).label('count')
            ).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).group_by(OperatorAction.priority).all()
            
            # Completed actions - use func.count() to avoid loading all columns
            completed_actions = self.db.query(func.count(OperatorAction.id)).filter(
                OperatorAction.status == 'completed',
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False)
            ).scalar() or 0
            
            # Average response time
            avg_response_time = self.db.query(
                func.avg(OperatorAction.response_time_minutes)
            ).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False),
                OperatorAction.response_time_minutes.isnot(None)
            ).scalar()
            
            # Average resolution time
            avg_resolution_time = self.db.query(
                func.avg(OperatorAction.resolution_time_minutes)
            ).filter(
                OperatorAction.action_timestamp >= cutoff_time,
                OperatorAction.is_deleted.is_(False),
                OperatorAction.resolution_time_minutes.isnot(None)
            ).scalar()
            
            # Completion rate
            completion_rate = (completed_actions / total_actions) if total_actions > 0 else 0
            
            return {
                'total_actions': total_actions,
                'completed_actions': completed_actions,
                'completion_rate': completion_rate,
                'average_response_time_minutes': float(avg_response_time) if avg_response_time else 0,
                'average_resolution_time_minutes': float(avg_resolution_time) if avg_resolution_time else 0,
                'type_distribution': {stat.action_type: stat.count for stat in type_stats},
                'status_distribution': {stat.status: stat.count for stat in status_stats},
                'priority_distribution': {stat.priority: stat.count for stat in priority_stats},
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting action statistics: {e}")
            raise
