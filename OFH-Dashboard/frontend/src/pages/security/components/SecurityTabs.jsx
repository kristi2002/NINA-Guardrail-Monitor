/**
 * Security Tab Navigation Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import './SecurityTabs.css'

const TAB_CONFIG = [
  { id: 'overview', icon: '🛡️' },
  { id: 'threats', icon: '⚠️' },
  { id: 'access', icon: '🔐' },
  { id: 'compliance', icon: '📋' },
  { id: 'incidents', icon: '🚨' },
  { id: 'alerting', icon: '📡' }
]

export default function SecurityTabs({ activeTab, onTabClick }) {
  const { t } = useTranslation()

  const tabs = useMemo(() => (
    TAB_CONFIG.map(tab => ({
      ...tab,
      label: t(`security.tabs.${tab.id}.label`)
    }))
  ), [t])

  return (
    <div className="security-tabs">
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

