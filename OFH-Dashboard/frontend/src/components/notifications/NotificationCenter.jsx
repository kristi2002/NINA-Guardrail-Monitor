import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNotifications } from '../../contexts/NotificationContext'
import './NotificationCenter.css'

function NotificationCenter({ isOpen, onClose }) {
  const { t, i18n } = useTranslation()
  const {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    clearError
  } = useNotifications()

  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('newest')
  const locale = i18n.language?.startsWith('it') ? 'it-IT' : 'en-US'

  const filterOptions = [
    { value: 'all', label: t('notificationCenter.filter.options.all') },
    { value: 'unread', label: t('notificationCenter.filter.options.unread') },
    { value: 'critical', label: t('notificationCenter.filter.options.critical') },
    { value: 'warning', label: t('notificationCenter.filter.options.warning') },
    { value: 'info', label: t('notificationCenter.filter.options.info') }
  ]

  const sortOptions = [
    { value: 'newest', label: t('notificationCenter.sort.options.newest') },
    { value: 'oldest', label: t('notificationCenter.sort.options.oldest') },
    { value: 'priority', label: t('notificationCenter.sort.options.priority') }
  ]

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true
    if (filter === 'unread') return !notification.read
    // Support both 'priority' and 'severity' fields
    const priority = notification.priority || notification.severity || 'info'
    if (filter === 'critical') return priority === 'critical' || priority === 'high'
    if (filter === 'warning') return priority === 'warning' || priority === 'medium'
    if (filter === 'info') return priority === 'info' || priority === 'low'
    return true
  })

  const sortedNotifications = [...filteredNotifications].sort((a, b) => {
    if (sortBy === 'newest') return new Date(b.timestamp) - new Date(a.timestamp)
    if (sortBy === 'oldest') return new Date(a.timestamp) - new Date(b.timestamp)
    if (sortBy === 'priority') {
      const priorityOrder = { critical: 3, warning: 2, info: 1 }
      return (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0)
    }
    return 0
  })

  const handleMarkAsRead = (notificationId) => {
    markAsRead(notificationId)
  }

  const handleMarkAllAsRead = () => {
    markAllAsRead()
  }

  const getPriorityIcon = (notification) => {
    // Support both 'priority' and 'severity' fields
    const priority = notification.priority || notification.severity || 'info'
    switch (priority) {
      case 'critical':
      case 'high': return '🚨'
      case 'warning':
      case 'medium': return '⚠️'
      case 'info':
      case 'low': return 'ℹ️'
      default: return '📢'
    }
  }

  const getPriorityColor = (notification) => {
    // Support both 'priority' and 'severity' fields
    const priority = notification.priority || notification.severity || 'info'
    switch (priority) {
      case 'critical':
      case 'high': return '#ef4444'
      case 'warning':
      case 'medium': return '#f59e0b'
      case 'info':
      case 'low': return '#3b82f6'
      default: return '#6b7280'
    }
  }
  
  const getPriorityLabel = (notification) => {
    // Support both 'priority' and 'severity' fields
    const priority = notification.priority || notification.severity || 'info'
    const key = (priority || 'info').toLowerCase()
    return t(`notificationCenter.priorityLabels.${key}`, { defaultValue: priority })
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return t('notificationCenter.timestamp.justNow')
    if (diffMins < 60) return t('notificationCenter.timestamp.minutes', { count: diffMins })
    if (diffHours < 24) return t('notificationCenter.timestamp.hours', { count: diffHours })
    if (diffDays < 7) return t('notificationCenter.timestamp.days', { count: diffDays })
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getTranslatedContent = (notification) => {
    const eventTypeRaw = (notification.metadata?.event_type || notification.type || 'default').toLowerCase()
    const eventKey = eventTypeRaw.replace(/[^a-z0-9]+/g, '_')
    const severityKey = (notification.severity || notification.priority || 'info').toLowerCase()
    const severityLabel = t(`notificationCenter.events.common.severity.${severityKey}`, {
      defaultValue: severityKey.toUpperCase()
    })
    const conversationId =
      notification.conversation_id ||
      notification.metadata?.conversation_id ||
      ''
    const eventId = notification.event_id || notification.metadata?.event_id || ''

    const guardrailRules = (notification.metadata?.guardrail_rules || [])
      .map(rule => rule?.name || rule?.rule_name || rule?.id || rule)
      .filter(Boolean)
    const violations = (notification.metadata?.violations || [])
      .map(violation => violation?.label || violation?.type || violation?.id || violation)
      .filter(Boolean)

    const ruleSummary = guardrailRules.length > 0
      ? `${t('notificationCenter.events.common.ruleSummary', {
          count: guardrailRules.length,
          rules: guardrailRules.join(', ')
        })} `
      : ''

    const violationSummary = violations.length > 0
      ? `${t('notificationCenter.events.common.violationSummary', {
          count: violations.length,
          violations: violations.join(', ')
        })} `
      : ''

    const originalMessageText = notification.message
      ? t('notificationCenter.events.common.originalMessage', { message: notification.message })
      : ''

    const params = {
      conversationId: conversationId || t('notificationCenter.events.common.unknownConversation'),
      eventId: eventId || t('notificationCenter.events.common.unknownEvent'),
      severityLabel,
      ruleSummary,
      violationSummary,
      originalMessage: originalMessageText
    }

    const titleKey = `notificationCenter.events.${eventKey}.title`
    const messageKey = `notificationCenter.events.${eventKey}.message`
    const defaultTitleKey = 'notificationCenter.events.default.title'
    const defaultMessageKey = 'notificationCenter.events.default.message'

    let title = i18n.exists(titleKey) ? t(titleKey, params) : ''
    if (!title || !title.trim()) {
      title = notification.title || t(defaultTitleKey, params)
    }

    let message = i18n.exists(messageKey) ? t(messageKey, params) : ''
    if (!message || !message.trim()) {
      message = notification.message || t(defaultMessageKey, params)
    }

    return {
      title: title.trim(),
      message: message.replace(/\s+/g, ' ').trim(),
      severityLabel
    }
  }

  if (!isOpen) return null

  return (
    <div className="notification-center-overlay">
      <div className="notification-center-modal">
        <div className="notification-center-header">
          <div className="header-left">
            <h2>🔔 {t('notificationCenter.title')}</h2>
            {unreadCount > 0 && (
              <span className="unread-badge">{unreadCount}</span>
            )}
          </div>
          <div className="header-right">
            {unreadCount > 0 && (
              <button
                className="mark-all-read-btn"
                onClick={handleMarkAllAsRead}
              >
                {t('notificationCenter.markAll')}
              </button>
            )}
            <button
              className="close-btn"
              onClick={onClose}
              aria-label={t('notificationCenter.close')}
            >
              ×
            </button>
          </div>
        </div>

        <div className="notification-center-filters">
          <div className="filter-group">
            <label>{t('notificationCenter.filter.label')}</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              {filterOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>{t('notificationCenter.sort.label')}</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
            <button onClick={clearError} className="clear-error-btn">
              {t('notificationCenter.error.dismiss')}
            </button>
          </div>
        )}

        <div className="notification-center-content">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>{t('notificationCenter.loading')}</p>
            </div>
          ) : sortedNotifications.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3>{t('notificationCenter.empty.title')}</h3>
              <p>{t('notificationCenter.empty.description')}</p>
            </div>
          ) : (
            <div className="notifications-list">
              {sortedNotifications.map((notification) => {
                const { title, message } = getTranslatedContent(notification)

                return (
                  <div
                    key={notification.id}
                    className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                    onClick={() => !notification.read && handleMarkAsRead(notification.id)}
                  >
                    <div className="notification-icon">
                      {getPriorityIcon(notification)}
                    </div>
                    
                    <div className="notification-content">
                      <div className="notification-header">
                        <h4 className="notification-title">
                          {title || notification.title || notification.message}
                        </h4>
                        <div className="notification-meta">
                          <span
                            className="priority-badge"
                            style={{ backgroundColor: getPriorityColor(notification) }}
                          >
                            {getPriorityLabel(notification)}
                          </span>
                          <span className="timestamp">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                        </div>
                      </div>
                      
                      <p className="notification-message">
                        {message || notification.message}
                      </p>
                    </div>
                    
                    {notification.actions && notification.actions.length > 0 && (
                      <div className="notification-actions">
                        {notification.actions.map((action, index) => (
                          <button
                            key={index}
                            className="action-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              action.onClick()
                            }}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}

                    {!notification.read && (
                      <div className="unread-indicator"></div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="notification-center-footer">
          <div className="notification-stats">
            <span>{t('notificationCenter.footer.total', { count: notifications.length })}</span>
            <span>{t('notificationCenter.footer.unread', { count: unreadCount })}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotificationCenter
