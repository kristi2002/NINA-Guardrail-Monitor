import { useState } from 'react'
import axios from 'axios'
import './Sidebar.css'

function Sidebar({ isOpen, onClose, alerts = [], onAlertsRefresh }) {
  const [acknowledgingAll, setAcknowledgingAll] = useState(false)

  const handleAcknowledgeAll = async () => {
    console.log('🚀 Acknowledge All button clicked')
    
    // Get all unacknowledged alerts
    const unacknowledgedAlerts = alerts.filter(alert => 
      alert.status !== 'acknowledged' && 
      alert.status !== 'ACKNOWLEDGED' && 
      alert.status !== 'resolved' && 
      alert.status !== 'RESOLVED'
    )
    
    if (unacknowledgedAlerts.length === 0) {
      alert('No unacknowledged alerts to process.')
      return
    }

    if (acknowledgingAll) {
      console.log('⚠️ Acknowledge All already in progress')
      return
    }

    try {
      setAcknowledgingAll(true)
      console.log(`📡 Acknowledging ${unacknowledgedAlerts.length} alerts...`)

      // Acknowledge all alerts in parallel
      const acknowledgePromises = unacknowledgedAlerts.map(alert => 
        axios.post(`/api/alerts/${alert.id}/acknowledge`, {
          operator_id: 'system'
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
      )

      const results = await Promise.allSettled(acknowledgePromises)
      
      const successful = results.filter(result => result.status === 'fulfilled').length
      const failed = results.filter(result => result.status === 'rejected').length

      if (successful > 0) {
        console.log(`🎉 Successfully acknowledged ${successful} alerts!`)
        
        // Show success message
        const message = failed > 0 
          ? `Successfully acknowledged ${successful} alerts. ${failed} failed.`
          : `Successfully acknowledged ${successful} alert${successful > 1 ? 's' : ''}!`
        
        // Create a more user-friendly notification
        const notification = document.createElement('div')
        notification.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          background: #10b981;
          color: white;
          padding: 1rem 1.5rem;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 10000;
          font-weight: 600;
          animation: slideIn 0.3s ease;
        `
        notification.textContent = message
        document.body.appendChild(notification)
        
        // Remove notification after 3 seconds
        setTimeout(() => {
          notification.style.animation = 'slideOut 0.3s ease'
          setTimeout(() => document.body.removeChild(notification), 300)
        }, 3000)
        
        // Refresh alerts after successful acknowledgment
        if (onAlertsRefresh) {
          onAlertsRefresh()
        }
      } else {
        console.log('❌ All acknowledge requests failed')
        alert('Failed to acknowledge alerts. Please try again.')
      }

    } catch (error) {
      console.error('💥 Failed to acknowledge all alerts:', error)
      alert('Failed to acknowledge alerts. Please try again.')
    } finally {
      setAcknowledgingAll(false)
      console.log('🏁 Acknowledge All process completed')
    }
  }
  return (
    <>
      {/* Overlay - darkens background when sidebar is open */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={onClose}></div>
      )}
      
      {/* Sidebar */}
      <div className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Sidebar Header */}
        <div className="sidebar-header">
          <h3>🚨 Alert Center</h3>
          <button className="sidebar-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Alert Summary */}
        <div className="alert-summary">
          <div className="summary-card critical">
            <span className="summary-icon">🔴</span>
            <div className="summary-info">
              <div className="summary-count">{alerts.filter(a => a.severity === 'critical' || a.severity === 'CRITICAL').length}</div>
              <div className="summary-label">Critical</div>
            </div>
          </div>
          
          <div className="summary-card high">
            <span className="summary-icon">🟠</span>
            <div className="summary-info">
              <div className="summary-count">{alerts.filter(a => a.severity === 'HIGH').length}</div>
              <div className="summary-label">High</div>
            </div>
          </div>
          
          <div className="summary-card medium">
            <span className="summary-icon">🟡</span>
            <div className="summary-info">
              <div className="summary-count">{alerts.filter(a => a.severity === 'MEDIUM').length}</div>
              <div className="summary-label">Medium</div>
            </div>
          </div>
        </div>

        {/* Alert List */}
        <div className="sidebar-content">
          {alerts.length === 0 ? (
            <div className="no-alerts-message">
              <div className="message-icon">✅</div>
              <h3>No Active Alerts</h3>
              <p>All systems are running normally. No alerts require immediate attention.</p>
            </div>
          ) : (
            <div className="alerts-list">
              <h4>Active Alerts ({alerts.length})</h4>
              {alerts.map((alert, index) => (
                <div key={alert.id || index} className={`alert-item ${alert.severity?.toLowerCase() || 'medium'}`}>
                  <div className="alert-header">
                    <span className={`alert-severity-badge ${alert.severity?.toLowerCase() || 'medium'}`}>
                      {alert.severity?.toUpperCase() || 'UNKNOWN'}
                    </span>
                    <span className="alert-time">
                      {new Date(alert.created_at).toLocaleTimeString('it-IT', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                  <div className="alert-message">
                    {alert.message || 'No message available'}
                  </div>
                  <div className="alert-details">
                    <div className="alert-patient">
                      {alert.patient_info?.name || `Conversation ${alert.conversation_id}`}
                    </div>
                    <div className="alert-status">
                      Status: <span className={`status-${alert.status?.toLowerCase() || 'unknown'}`}>
                        {alert.status?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </div>
                    {alert.assigned_to && (
                      <div className="alert-assigned">
                        Assigned to: {alert.assigned_to}
                      </div>
                    )}
                    {alert.tags && alert.tags.length > 0 && (
                      <div className="alert-tags">
                        {alert.tags.map((tag, tagIndex) => (
                          <span key={tagIndex} className="alert-tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <button 
            className="btn-acknowledge-all"
            onClick={handleAcknowledgeAll}
            disabled={acknowledgingAll || alerts.filter(a => 
              a.status !== 'acknowledged' && 
              a.status !== 'ACKNOWLEDGED' && 
              a.status !== 'resolved' && 
              a.status !== 'RESOLVED'
            ).length === 0}
          >
            {acknowledgingAll ? (
              <>
                <span className="loading-spinner small"></span>
                Processing...
              </>
            ) : (
              <>
                ✓ Acknowledge All ({alerts.filter(a => 
                  a.status !== 'acknowledged' && 
                  a.status !== 'ACKNOWLEDGED' && 
                  a.status !== 'resolved' && 
                  a.status !== 'RESOLVED'
                ).length})
              </>
            )}
          </button>
        </div>
      </div>
    </>
  )
}

export default Sidebar
