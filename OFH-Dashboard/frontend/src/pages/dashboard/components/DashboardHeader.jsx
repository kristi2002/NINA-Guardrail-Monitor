/**
 * Dashboard Header Component
 */
import { TimeAgo } from '../../../components/ui'
import './DashboardHeader.css'

export default function DashboardHeader({ lastUpdated }) {
  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="header-title">
          <h1>Monitoraggio conversazioni</h1>
          <span className="header-subtitle">Sistema di monitoraggio real-time per conversazioni terapeutiche</span>
        </div>
        
        <div className="system-status">
          <span className="status-indicator status-online"></span>
          <span className="status-text">System Online</span>
          <span className="status-divider">|</span>
          <TimeAgo timestamp={lastUpdated} />
        </div>
      </div>
      
      <div className="header-right">
        {/* Reserved for future dashboard controls */}
      </div>
    </div>
  )
}

