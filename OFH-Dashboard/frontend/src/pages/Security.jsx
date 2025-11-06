import React, { useState } from 'react'
import { SecurityHeader, SecurityTabs } from './security/components'
import { OverviewTab, ThreatsTab, AccessTab, ComplianceTab, IncidentsTab } from './security/tabs'
import { useSecurityData } from './security/hooks'
import { useTabNavigation } from '../hooks/shared'
import { getSecurityData } from './security/utils/getSecurityData'
import './security/Security.css'

const Security = () => {
  const [timeRange, setTimeRange] = useState('7d')
  const { activeTab, handleTabClick } = useTabNavigation('overview')
  
  const {
    securityData,
    loading,
    error,
    lastUpdated,
    fetchSecurityData
  } = useSecurityData(activeTab, timeRange)

  // Helper for rendering metric cards (used by tab components)
  const renderMetricCard = (title, value, subtitle, icon, trend) => (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
        {trend && <span className={`metric-trend ${trend.type}`}>{trend.value}</span>}
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-subtitle">{subtitle}</div>
    </div>
  )

  // Render tab based on active tab
  const renderTabContent = () => {
    // Only get safe data if we have actual data (not null or empty object)
    const hasData = securityData && Object.keys(securityData).length > 0
    const safeData = hasData ? getSecurityData(securityData) : null
    const tabProps = {
      data: safeData,
      loading,
      renderMetricCard,
      securityDataRaw: securityData // Pass raw data so components can check if it's null/empty
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewTab {...tabProps} />
      case 'threats':
        return <ThreatsTab {...tabProps} />
      case 'access':
        return <AccessTab {...tabProps} />
      case 'compliance':
        return <ComplianceTab {...tabProps} />
      case 'incidents':
        return <IncidentsTab {...tabProps} />
      default:
        return <OverviewTab {...tabProps} />
    }
  }

  // Loading state
  if (loading && !securityData) {
    return <div className="security-loading">Loading security dashboard...</div>
  }

  return (
    <div className="security-dashboard">
      <SecurityHeader 
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        lastUpdated={lastUpdated}
      />

      <SecurityTabs 
        activeTab={activeTab}
        onTabClick={handleTabClick}
      />

      <div className="security-content">
        {error && (
          <div className="security-error-banner" style={{ padding: '1rem', background: '#fee', color: '#c33', marginBottom: '1rem', borderRadius: '4px' }}>
            ⚠️ {error}
            <button onClick={() => fetchSecurityData(true)} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem' }}>Retry</button>
          </div>
        )}
        {loading && securityData && (
          <div className="security-loading-indicator" style={{ padding: '1rem', textAlign: 'center' }}>Loading {activeTab} data...</div>
        )}
        {renderTabContent()}
      </div>
    </div>
  )
}

export default Security
