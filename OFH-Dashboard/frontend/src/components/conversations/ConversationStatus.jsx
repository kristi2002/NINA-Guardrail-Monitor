import { useState, useEffect } from 'react'
import './ConversationStatus.css'

function ConversationStatus({ conversations = [] }) {
  const [statusCounts, setStatusCounts] = useState({
    total: 0,
    active: 0,
    warning: 0,
    danger: 0,
    completed: 0
  })

  // isLive state removed as real-time indicator was removed

  useEffect(() => {
    // Calculate status counts from conversations
    const counts = {
      total: conversations.length,
      active: conversations.filter(c => c.status === 'IN_PROGRESS').length,
      warning: conversations.filter(c => c.situationLevel === 'medium').length,
      danger: conversations.filter(c => c.situationLevel === 'high').length,
      completed: conversations.filter(c => c.status === 'COMPLETED').length
    }
    
    setStatusCounts(counts)
  }, [conversations])

  const getStatusConfig = (type) => {
    const configs = {
      total: {
        label: 'Totale',
        icon: '📊',
        class: 'status-total',
        color: '#1976d2'
      },
      active: {
        label: 'Attive',
        icon: '⚡',
        class: 'status-active',
        color: '#4caf50'
      },
      warning: {
        label: 'Attenzione',
        icon: '⚠️',
        class: 'status-warning',
        color: '#ffa726'
      },
      danger: {
        label: 'Pericolo',
        icon: '🚨',
        class: 'status-danger',
        color: '#f44336'
      },
      completed: {
        label: 'Completate',
        icon: '✅',
        class: 'status-completed',
        color: '#2e7d32'
      }
    }
    return configs[type] || configs.total
  }

  const getOverallStatus = () => {
    if (statusCounts.danger > 0) {
      return {
        level: 'danger',
        message: 'Livello massimo di pericolosità rilevato',
        color: '#f44336',
        icon: '🚨'
      }
    } else if (statusCounts.warning > 0) {
      return {
        level: 'warning',
        message: 'Situazioni di attenzione rilevate',
        color: '#ffa726',
        icon: '⚠️'
      }
    } else if (statusCounts.active > 0) {
      return {
        level: 'active',
        message: 'Tutto regolare',
        color: '#4caf50',
        icon: '👍'
      }
    } else {
      return {
        level: 'inactive',
        message: 'Nessuna conversazione attiva',
        color: '#9e9e9e',
        icon: '💤'
      }
    }
  }

  const overallStatus = getOverallStatus()

  return (
    <div className="conversation-status">
      {/* Real-time indicator removed as requested */}

      {/* Overall Status */}
      <div className={`overall-status ${overallStatus.level}`}>
        <div className="status-icon">{overallStatus.icon}</div>
        <div className="status-content">
          <h3>{overallStatus.message}</h3>
          <p>
            {statusCounts.total} conversazioni monitorate
            {statusCounts.danger > 0 && ` • ${statusCounts.danger} in pericolo`}
            {statusCounts.warning > 0 && statusCounts.danger === 0 && ` • ${statusCounts.warning} richiedono attenzione`}
          </p>
        </div>
      </div>

      {/* Status Grid */}
      <div className="status-grid">
        {Object.entries(statusCounts).map(([key, count]) => {
          const config = getStatusConfig(key)
          return (
            <div key={key} className={`status-card ${config.class}`}>
              <div className="status-card-icon">{config.icon}</div>
              <div className="status-card-content">
                <div className="status-count">{count}</div>
                <div className="status-label">{config.label}</div>
              </div>
              <div className="status-trend">
                {count > 0 && (
                  <span className="trend-indicator up">↗</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Alternative status boxes removed as requested */}
    </div>
  )
}

export default ConversationStatus
