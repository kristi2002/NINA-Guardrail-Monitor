import { useState, useEffect, useRef } from 'react'
import { AnalyticsHeader, AnalyticsTabs } from './analytics/components'
import { MetricCard } from '../components/analytics'
import { OverviewTab, NotificationsTab, UsersTab, AlertsTab, ResponseTimesTab, EscalationsTab, GuardrailPerformanceTab } from './analytics/tabs'
import { useAnalyticsData } from './analytics/hooks'
import { useTabNavigation } from '../hooks/shared'
import { exportAnalyticsData } from './analytics/utils/exportData'
import './analytics/Analytics.css'

function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')
  const [exporting, setExporting] = useState(false)
  const { activeTab, handleTabClick } = useTabNavigation('overview')
  
  // Force style recalculation on mount to ensure CSS is properly applied
  useEffect(() => {
    // Force a reflow to ensure styles are applied
    const analyticsPage = document.querySelector('.analytics-page')
    if (analyticsPage) {
      // Trigger a reflow by reading offsetHeight
      void analyticsPage.offsetHeight
      // Ensure font-family and text-align are set
      analyticsPage.style.fontFamily = "'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
      analyticsPage.style.textAlign = 'left'
    }
  }, [])
  
  const {
    analyticsData,
    loading,
    error,
    lastUpdated,
    fetchAnalyticsData
  } = useAnalyticsData(activeTab, timeRange)

  const handleExport = async () => {
    if (!analyticsData) {
      alert('No data available to export. Please wait for data to load.')
      return
    }
    
    setExporting(true)
    try {
      await exportAnalyticsData(activeTab, timeRange, 'json', analyticsData)
    } finally {
      setExporting(false)
    }
  }

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
    const tabProps = {
      data: analyticsData,
      loading,
      renderMetricCard
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewTab {...tabProps} timeRange={timeRange} />
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
      case 'guardrail-performance':
        return <GuardrailPerformanceTab {...tabProps} />
      default:
        return <OverviewTab {...tabProps} timeRange={timeRange} />
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
        exporting={exporting}
        hasData={!!analyticsData}
      />

      <AnalyticsTabs 
        activeTab={activeTab}
        onTabClick={handleTabClick}
      />

      {/* Tab Content */}
      <div className={`analytics-content ${animateContent ? 'content-transition' : ''}`}>
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
