import { useState, useEffect } from 'react'
import { useNotifications } from '../../contexts/NotificationContext'
import './NotificationCenter.css'

function NotificationCenter({ isOpen, onClose }) {
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
    switch (priority) {
      case 'critical': return 'critical'
      case 'high': return 'high'
      case 'warning': return 'warning'
      case 'medium': return 'medium'
      case 'info': return 'info'
      case 'low': return 'low'
      default: return 'info'
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (!isOpen) return null

  return (
    <div className="notification-center-overlay">
      <div className="notification-center-modal">
        <div className="notification-center-header">
          <div className="header-left">
            <h2>🔔 Notifications</h2>
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
                Mark all as read
              </button>
            )}
            <button
              className="close-btn"
              onClick={onClose}
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        <div className="notification-center-filters">
          <div className="filter-group">
            <label>Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All</option>
              <option value="unread">Unread</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
              <option value="priority">Priority</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
            <button onClick={clearError} className="clear-error-btn">
              ×
            </button>
          </div>
        )}

        <div className="notification-center-content">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading notifications...</p>
            </div>
          ) : sortedNotifications.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3>No notifications</h3>
              <p>You're all caught up! New notifications will appear here.</p>
            </div>
          ) : (
            <div className="notifications-list">
              {sortedNotifications.map((notification) => (
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
                        {notification.title || notification.message}
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
                      {notification.message}
                    </p>
                    
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
                  </div>
                  
                  {!notification.read && (
                    <div className="unread-indicator"></div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="notification-center-footer">
          <div className="notification-stats">
            <span>Total: {notifications.length}</span>
            <span>Unread: {unreadCount}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotificationCenter
