/**
 * Analytics Tab Navigation Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import './AnalyticsTabs.css'

const TAB_CONFIG = [
  { id: 'overview', icon: '📊' },
  { id: 'notifications', icon: '📧' },
  { id: 'users', icon: '👥' },
  { id: 'alerts', icon: '📈' },
  { id: 'response', icon: '⏱️' },
  { id: 'escalations', icon: '⬆️' },
  { id: 'guardrail-performance', icon: '🛡️' }
]

export default function AnalyticsTabs({ activeTab, onTabClick }) {
  const { t } = useTranslation()

  const tabs = useMemo(() => (
    TAB_CONFIG.map(tab => ({
      ...tab,
      label: t(`analytics.tabs.${tab.id}.label`)
    }))
  ), [t])

  return (
    <div className="analytics-tabs">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabClick(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  )
}

