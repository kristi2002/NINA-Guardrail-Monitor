import { useState } from 'react'
import { AnalyticsHeader, AnalyticsTabs } from './analytics/components'
import { OverviewTab, NotificationsTab, UsersTab, AlertsTab, ResponseTimesTab, EscalationsTab } from './analytics/tabs'
import { useAnalyticsData } from './analytics/hooks'
import { useTabNavigation } from '../hooks/shared'
import { exportAnalyticsData } from './analytics/utils/exportData'
import './analytics/Analytics.css'

function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')
  const { activeTab, handleTabClick } = useTabNavigation('overview')
  
  const {
    analyticsData,
    loading,
    error,
    lastUpdated,
    fetchAnalyticsData
  } = useAnalyticsData(activeTab, timeRange)

  const handleExport = () => exportAnalyticsData(timeRange, 'json')

  // Helper for rendering metric cards (used by tab components)
  const renderMetricCard = (title, value, subtitle, icon, trend) => (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      {trend !== undefined && (
        <div className={`metric-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
          {trend >= 0 ? '↗️' : '↘️'} {Math.abs(trend)}%
        </div>
      )}
    </div>
  )

  // Render tab based on active tab
  const renderTabContent = () => {
    const tabProps = {
      data: analyticsData,
      loading,
      renderMetricCard
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewTab {...tabProps} />
      case 'notifications':
        return <NotificationsTab {...tabProps} />
      case 'users':
        return <UsersTab {...tabProps} />
      case 'alerts':
        return <AlertsTab {...tabProps} />
      case 'response':
        return <ResponseTimesTab {...tabProps} />
      case 'escalations':
        return <EscalationsTab {...tabProps} />
      default:
        return <OverviewTab {...tabProps} />
    }
  }

  // Loading state
  if (loading && !analyticsData) {
    return <div className="analytics-loading">Loading analytics dashboard...</div>
  }

  return (
    <div className="analytics-page">
      <AnalyticsHeader 
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        onExport={handleExport}
        lastUpdated={lastUpdated}
      />

      <AnalyticsTabs 
        activeTab={activeTab}
        onTabClick={handleTabClick}
      />

      {/* Tab Content */}
      <div className="analytics-content">
        {error && (
          <div className="analytics-error-banner" style={{ padding: '1rem', background: '#fee', color: '#c33', marginBottom: '1rem', borderRadius: '4px' }}>
            ⚠️ {error}
            <button onClick={() => { fetchAnalyticsData(); }} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem' }}>Retry</button>
          </div>
        )}
        {loading && analyticsData && (
          <div className="analytics-loading-indicator" style={{ padding: '1rem', textAlign: 'center' }}>Loading {activeTab} data...</div>
        )}
        {renderTabContent()}
      </div>
    </div>
  )
}

export default Analytics
