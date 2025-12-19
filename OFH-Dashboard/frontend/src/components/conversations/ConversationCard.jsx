/**
 * Memoized Conversation Card Component
 */

import React, { memo, useMemo, useCallback } from 'react';
import { useAuth } from '../../contexts';
import './ConversationCard.css';

const ConversationCard = memo(({ 
  conversation, 
  onSelect, 
  onAcknowledge, 
  onEscalate, 
  onClose,
  isSelected = false,
  showActions = true 
}) => {
  const { user } = useAuth();

  // Memoize formatted date
  const formattedDate = useMemo(() => {
    const dateStr = conversation?.session_start || conversation?.start_time || conversation?.created_at;
    if (!dateStr) return 'N/A';
    
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return 'Invalid Date';
      
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Invalid Date';
    }
  }, [conversation?.session_start, conversation?.start_time, conversation?.created_at]);

  // Memoize risk level styling
  const riskLevelStyle = useMemo(() => {
    const risk = (conversation?.situationLevel || conversation?.risk_level || 'low').toLowerCase();
    const styles = {
      low: { color: '#10b981', backgroundColor: '#d1fae5' },
      medium: { color: '#f59e0b', backgroundColor: '#fef3c7' },
      high: { color: '#ef4444', backgroundColor: '#fee2e2' },
      critical: { color: '#dc2626', backgroundColor: '#fecaca' }
    };
    return styles[risk] || styles.low;
  }, [conversation?.situationLevel, conversation?.risk_level]);

  // Memoize status styling
  const statusStyle = useMemo(() => {
    const status = conversation?.status?.toLowerCase() || 'active';
    const styles = {
      active: { color: '#059669', backgroundColor: '#d1fae5' },
      pending: { color: '#d97706', backgroundColor: '#fef3c7' },
      resolved: { color: '#6b7280', backgroundColor: '#f3f4f6' },
      escalated: { color: '#dc2626', backgroundColor: '#fee2e2' },
      closed: { color: '#374151', backgroundColor: '#e5e7eb' },
      false_alarm: { color: '#7c3aed', backgroundColor: '#ede9fe' }
    };
    return styles[status] || styles.active;
  }, [conversation?.status]);

  // Memoize patient name
  const patientName = useMemo(() => {
    return conversation?.patientInfo?.name || 'Unknown Patient';
  }, [conversation?.patientInfo?.name]);

  // Memoize conversation summary
  const conversationSummary = useMemo(() => {
    const summary = conversation?.summary || conversation?.situation || 'No summary available';
    if (summary === 'No summary available') return summary;
    
    const maxLength = 150;
    if (summary.length <= maxLength) {
      return summary;
    }
    
    return summary.substring(0, maxLength) + '...';
  }, [conversation?.summary, conversation?.situation]);

  // Check if conversation has evasion/jailbreak attempts
  const hasEvasionAttempt = useMemo(() => {
    const events = conversation?.events || conversation?.recent_events || [];
    const evasionTypes = ['persistent_evasion', 'jailbreak_attempt', 'security_bypass_attempt'];
    return events.some(event => {
      const eventType = event?.event_type || event?.type || '';
      return evasionTypes.some(type => eventType.toLowerCase().includes(type.toLowerCase()));
    });
  }, [conversation?.events, conversation?.recent_events]);

  // Memoized event handlers
  const handleSelect = useCallback(() => {
    onSelect?.(conversation);
  }, [conversation, onSelect]);

  const handleAcknowledge = useCallback((e) => {
    e.stopPropagation();
    onAcknowledge?.(conversation);
  }, [conversation, onAcknowledge]);

  const handleEscalate = useCallback((e) => {
    e.stopPropagation();
    onEscalate?.(conversation);
  }, [conversation, onEscalate]);

  const handleClose = useCallback((e) => {
    e.stopPropagation();
    onClose?.(conversation);
  }, [conversation, onClose]);

  // Memoized action buttons
  const actionButtons = useMemo(() => {
    if (!showActions) return null;

    return (
      <div className="conversation-card-actions">
        {conversation?.status === 'ACTIVE' && (
          <>
            <button
              className="btn-acknowledge"
              onClick={handleAcknowledge}
              title="Acknowledge conversation"
            >
              ✓ Acknowledge
            </button>
            <button
              className="btn-escalate"
              onClick={handleEscalate}
              title="Escalate conversation"
            >
              ⚠ Escalate
            </button>
          </>
        )}
        {conversation?.status === 'ACTIVE' && (
          <button
            className="btn-close"
            onClick={handleClose}
            title="Close conversation"
          >
            ✕ Close
          </button>
        )}
      </div>
    );
  }, [
    showActions,
    conversation?.status,
    handleAcknowledge,
    handleEscalate,
    handleClose
  ]);

  return (
    <div 
      className={`conversation-card ${isSelected ? 'selected' : ''}`}
      onClick={handleSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSelect();
        }
      }}
    >
      <div className="conversation-card-header">
        <div className="conversation-card-title">
          <h3>{patientName}</h3>
          <span className="conversation-id">#{conversation?.id || conversation?.session_id}</span>
        </div>
        <div className="conversation-card-meta">
          <span className="conversation-date">{formattedDate}</span>
        </div>
      </div>

      <div className="conversation-card-body">
        <div className="conversation-card-status">
          <span 
            className="status-badge"
            style={statusStyle}
          >
            {conversation?.status || 'Unknown'}
          </span>
          <span 
            className="risk-badge"
            style={riskLevelStyle}
          >
            {conversation?.situationLevel || conversation?.risk_level || 'Low'} Risk
          </span>
          {hasEvasionAttempt && (
            <span 
              className="evasion-badge"
              style={{ color: '#dc2626', backgroundColor: '#fee2e2', border: '1px solid #dc2626' }}
              title="Security threat detected: Evasion/jailbreak attempt"
            >
              🛡️ Security Threat
            </span>
          )}
        </div>

        <div className="conversation-card-summary">
          <p>{conversationSummary}</p>
        </div>

        {conversation?.situation && (
          <div className="conversation-card-situation">
            <strong>Situation:</strong> {conversation.situation}
          </div>
        )}
      </div>

      {actionButtons}
    </div>
  );
});

ConversationCard.displayName = 'ConversationCard';

export default ConversationCard;

