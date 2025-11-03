/**
 * Memoized Alert Card Component
 */

import React, { memo, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts';
import './AlertCard.css';

const AlertCard = memo(({ 
  alert, 
  onAcknowledge, 
  onResolve, 
  onEscalate,
  onSelect,
  isSelected = false,
  showActions = true 
}) => {
  const { user } = useAuth();

  // Memoize formatted date
  const formattedDate = useMemo(() => {
    if (!alert?.triggered_at) return 'N/A';
    
    try {
      const date = new Date(alert.triggered_at);
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
  }, [alert?.triggered_at]);

  // Memoize severity styling
  const severityStyle = useMemo(() => {
    const severity = alert?.severity?.toLowerCase() || 'medium';
    const styles = {
      low: { 
        color: '#059669', 
        backgroundColor: '#d1fae5',
        borderColor: '#10b981'
      },
      medium: { 
        color: '#d97706', 
        backgroundColor: '#fef3c7',
        borderColor: '#f59e0b'
      },
      high: { 
        color: '#dc2626', 
        backgroundColor: '#fee2e2',
        borderColor: '#ef4444'
      },
      critical: { 
        color: '#7c2d12', 
        backgroundColor: '#fed7aa',
        borderColor: '#ea580c'
      }
    };
    return styles[severity] || styles.medium;
  }, [alert?.severity]);

  // Memoize status styling
  const statusStyle = useMemo(() => {
    const status = alert?.status?.toLowerCase() || 'active';
    const styles = {
      active: { 
        color: '#dc2626', 
        backgroundColor: '#fee2e2',
        borderColor: '#ef4444'
      },
      acknowledged: { 
        color: '#d97706', 
        backgroundColor: '#fef3c7',
        borderColor: '#f59e0b'
      },
      resolved: { 
        color: '#059669', 
        backgroundColor: '#d1fae5',
        borderColor: '#10b981'
      },
      escalated: { 
        color: '#7c3aed', 
        backgroundColor: '#ede9fe',
        borderColor: '#8b5cf6'
      },
      closed: { 
        color: '#6b7280', 
        backgroundColor: '#f3f4f6',
        borderColor: '#9ca3af'
      }
    };
    return styles[status] || styles.active;
  }, [alert?.status]);

  // Memoize alert description
  const alertDescription = useMemo(() => {
    if (!alert?.description) return 'No description available';
    
    const maxLength = 200;
    if (alert.description.length <= maxLength) {
      return alert.description;
    }
    
    return alert.description.substring(0, maxLength) + '...';
  }, [alert?.description]);

  // Memoize time since alert
  const timeSinceAlert = useMemo(() => {
    if (!alert?.triggered_at) return 'Unknown';
    
    try {
      const alertTime = new Date(alert.triggered_at);
      const now = new Date();
      const diffMs = now - alertTime;
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMinutes / 60);
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffDays > 0) {
        return `${diffDays}d ago`;
      } else if (diffHours > 0) {
        return `${diffHours}h ago`;
      } else if (diffMinutes > 0) {
        return `${diffMinutes}m ago`;
      } else {
        return 'Just now';
      }
    } catch (error) {
      console.error('Time calculation error:', error);
      return 'Unknown';
    }
  }, [alert?.triggered_at]);

  // Memoized event handlers
  const handleSelect = useCallback(() => {
    onSelect?.(alert);
  }, [alert, onSelect]);

  const handleAcknowledge = useCallback((e) => {
    e.stopPropagation();
    onAcknowledge?.(alert);
  }, [alert, onAcknowledge]);

  const handleResolve = useCallback((e) => {
    e.stopPropagation();
    onResolve?.(alert);
  }, [alert, onResolve]);

  const handleEscalate = useCallback((e) => {
    e.stopPropagation();
    onEscalate?.(alert);
  }, [alert, onEscalate]);

  // Memoized action buttons
  const actionButtons = useMemo(() => {
    if (!showActions) return null;

    const buttons = [];

    if (alert?.status === 'ACTIVE') {
      buttons.push(
        <button
          key="acknowledge"
          className="btn-acknowledge"
          onClick={handleAcknowledge}
          title="Acknowledge alert"
        >
          ✓ Acknowledge
        </button>
      );
    }

    if (alert?.status === 'ACKNOWLEDGED' || alert?.status === 'ACTIVE') {
      buttons.push(
        <button
          key="resolve"
          className="btn-resolve"
          onClick={handleResolve}
          title="Resolve alert"
        >
          ✓ Resolve
        </button>
      );
    }

    if (alert?.status === 'ACTIVE' || alert?.status === 'ACKNOWLEDGED') {
      buttons.push(
        <button
          key="escalate"
          className="btn-escalate"
          onClick={handleEscalate}
          title="Escalate alert"
        >
          ⚠ Escalate
        </button>
      );
    }

    return buttons.length > 0 ? (
      <div className="alert-card-actions">
        {buttons}
      </div>
    ) : null;
  }, [
    showActions,
    alert?.status,
    handleAcknowledge,
    handleResolve,
    handleEscalate
  ]);

  return (
    <div 
      className={`alert-card ${isSelected ? 'selected' : ''}`}
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
      <div className="alert-card-header">
        <div className="alert-card-title">
          <h3>{alert?.title || 'Untitled Alert'}</h3>
          <span className="alert-id">#{alert?.alert_id}</span>
        </div>
        <div className="alert-card-meta">
          <span className="alert-date">{formattedDate}</span>
          <span className="alert-time-ago">{timeSinceAlert}</span>
        </div>
      </div>

      <div className="alert-card-body">
        <div className="alert-card-status">
          <span 
            className="severity-badge"
            style={severityStyle}
          >
            {alert?.severity || 'Medium'}
          </span>
          <span 
            className="status-badge"
            style={statusStyle}
          >
            {alert?.status || 'Active'}
          </span>
        </div>

        <div className="alert-card-description">
          <p>{alertDescription}</p>
        </div>

        {alert?.assigned_to && (
          <div className="alert-card-assignment">
            <strong>Assigned to:</strong> {alert.assigned_to}
          </div>
        )}

        {alert?.patient_info && (
          <div className="alert-card-patient">
            <strong>Patient:</strong> {alert.patient_info.name || 'Unknown'}
          </div>
        )}
      </div>

      {actionButtons}
    </div>
  );
});

AlertCard.displayName = 'AlertCard';

export default AlertCard;

