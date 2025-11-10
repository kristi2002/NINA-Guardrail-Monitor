/**
 * Dashboard Header Component
 */
import { useTranslation } from 'react-i18next'
import { TimeAgo } from '../../../components/ui'
import './DashboardHeader.css'

export default function DashboardHeader({ lastUpdated }) {
  const { t } = useTranslation()

  return (
    <div className="dashboard-header">
      <div className="header-left">
        <div className="header-title">
          <h1>{t('dashboard.header.title')}</h1>
          <span className="header-subtitle">{t('dashboard.header.subtitle')}</span>
        </div>
        
        <div className="system-status">
          <span className="status-indicator status-online"></span>
          <span className="status-text">{t('dashboard.header.systemOnline')}</span>
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

