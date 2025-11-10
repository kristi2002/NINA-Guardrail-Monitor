import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { SecurityHeader, SecurityTabs } from './security/components'
import { MetricCard } from '../components/analytics'
import { OverviewTab, ThreatsTab, AccessTab, ComplianceTab, IncidentsTab, AlertingTab } from './security/tabs'
import { useSecurityData } from './security/hooks'
import { useTabNavigation } from '../hooks/shared'
import { getSecurityData } from './security/utils/getSecurityData'
import './security/Security.css'

const Security = () => {
  const { t } = useTranslation()
  const [timeRange, setTimeRange] = useState('7d')
  const { activeTab, handleTabClick } = useTabNavigation('overview')
  
  const {
    securityData,
    loading,
    error,
    lastUpdated,
    fetchSecurityData
  } = useSecurityData(activeTab, timeRange)

  const [animateContent, setAnimateContent] = useState(false)
  const prevLoadingRef = useRef(loading)

  useEffect(() => {
    if (prevLoadingRef.current && !loading) {
      setTimeout(() => setAnimateContent(true), 0)
      const timer = setTimeout(() => setAnimateContent(false), 450)
      return () => clearTimeout(timer)
    }
    prevLoadingRef.current = loading
  }, [loading])

  // Helper for rendering metric cards (used by tab components)
  const renderMetricCard = (title, value, subtitle, icon, trend, options = {}) => (
    <MetricCard
      title={title}
      value={value}
      subtitle={subtitle}
      icon={icon}
      trend={trend}
      isAlert={options.isAlert}
    />
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
      case 'alerting':
        return <AlertingTab {...tabProps} />
      default:
        return <OverviewTab {...tabProps} />
    }
  }

  // Loading state
  if (loading && !securityData) {
    return <div className="security-loading">{t('security.messages.loading')}</div>
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

      <div className={`security-content ${animateContent ? 'content-transition' : ''}`}>
        {error && (
          <div className="security-error-banner" style={{ padding: '1rem', background: '#fee', color: '#c33', marginBottom: '1rem', borderRadius: '4px' }}>
            {t('security.messages.errorPrefix')} {error}
            <button onClick={() => fetchSecurityData(true)} style={{ marginLeft: '1rem', padding: '0.25rem 0.5rem' }}>
              {t('security.messages.retry')}
            </button>
          </div>
        )}
        {loading && securityData && (
          <div className="security-loading-indicator" style={{ padding: '1rem', textAlign: 'center' }}>
            {t('security.messages.loadingTab', { tab: t(`security.tabs.${activeTab}.label`) })}
          </div>
        )}
        {renderTabContent()}
      </div>
    </div>
  )
}

export default Security
