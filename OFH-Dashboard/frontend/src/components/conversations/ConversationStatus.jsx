import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import './ConversationStatus.css'

function ConversationStatus({ conversations = [] }) {
  const { t } = useTranslation()
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

  const statusConfigs = useMemo(() => ({
    total: {
      label: t('conversationStatus.cards.total'),
      icon: '📊',
      class: 'status-total',
      color: '#1976d2'
    },
    active: {
      label: t('conversationStatus.cards.active'),
      icon: '⚡',
      class: 'status-active',
      color: '#4caf50'
    },
    warning: {
      label: t('conversationStatus.cards.warning'),
      icon: '⚠️',
      class: 'status-warning',
      color: '#ffa726'
    },
    danger: {
      label: t('conversationStatus.cards.danger'),
      icon: '🚨',
      class: 'status-danger',
      color: '#f44336'
    },
    completed: {
      label: t('conversationStatus.cards.completed'),
      icon: '✅',
      class: 'status-completed',
      color: '#2e7d32'
    }
  }), [t])

  const overallStatus = useMemo(() => {
    if (statusCounts.danger > 0) {
      return {
        level: 'danger',
        message: t('conversationStatus.overall.danger'),
        color: '#f44336',
        icon: '🚨'
      }
    }
    if (statusCounts.warning > 0) {
      return {
        level: 'warning',
        message: t('conversationStatus.overall.warning'),
        color: '#ffa726',
        icon: '⚠️'
      }
    }
    if (statusCounts.active > 0) {
      return {
        level: 'active',
        message: t('conversationStatus.overall.active'),
        color: '#4caf50',
        icon: '👍'
      }
    }
    return {
      level: 'inactive',
      message: t('conversationStatus.overall.inactive'),
      color: '#9e9e9e',
      icon: '💤'
    }
  }, [statusCounts.active, statusCounts.danger, statusCounts.warning, t])

  const monitoredSummary = t('conversationStatus.overall.summary.monitored', {
    count: statusCounts.total
  })
  const dangerSummary =
    statusCounts.danger > 0
      ? t('conversationStatus.overall.summary.danger', { count: statusCounts.danger })
      : ''
  const warningSummary =
    statusCounts.warning > 0 && statusCounts.danger === 0
      ? t('conversationStatus.overall.summary.warning', { count: statusCounts.warning })
      : ''

  return (
    <div className="conversation-status">
      {/* Real-time indicator removed as requested */}

      {/* Overall Status */}
      <div className={`overall-status ${overallStatus.level}`}>
        <div className="status-icon">{overallStatus.icon}</div>
        <div className="status-content">
          <h3>{overallStatus.message}</h3>
          <p>
            {monitoredSummary}
            {dangerSummary && ` • ${dangerSummary}`}
            {warningSummary && ` • ${warningSummary}`}
          </p>
        </div>
      </div>

      {/* Status Grid */}
      <div className="status-grid">
        {Object.entries(statusCounts).map(([key, count]) => {
          const config = statusConfigs[key] || statusConfigs.total
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
