/**
 * Dashboard Header Component
 */
import { TimeAgo } from '../../../components/ui'
import './DashboardHeader.css'

export default function DashboardHeader({ alerts, lastUpdated, onOpenSidebar }) {
  const criticalAlertsCount = alerts.filter(
    alert => alert.severity === 'critical' || alert.severity === 'CRITICAL'
  ).length

  return (
    <div className={`dashboard-header ${criticalAlertsCount > 0 ? 'has-critical-alerts' : ''}`}>
      <div className="header-left">
        <div className="header-title">
          <h1>Monitoraggio conversazioni</h1>
          <span className="header-subtitle">Sistema di monitoraggio real-time per conversazioni terapeutiche</span>
        </div>
        
        {/* Critical Alert Indicator */}
        {criticalAlertsCount > 0 && (
          <div className="critical-alert-indicator">
            <span className="alert-icon">🚨</span>
            <span className="alert-text">
              {criticalAlertsCount} Critical Alert(s) - 
              <button 
                className="btn-view-critical-alerts"
                onClick={onOpenSidebar}
              >
                View Now
              </button>
            </span>
          </div>
        )}
        
        <div className="system-status">
          <span className="status-indicator status-online"></span>
          <span className="status-text">System Online</span>
          <span className="status-divider">|</span>
          <TimeAgo timestamp={lastUpdated} />
        </div>
      </div>
      
      <div className="header-right">
        {/* Alert button removed as requested */}
      </div>
    </div>
  )
}

