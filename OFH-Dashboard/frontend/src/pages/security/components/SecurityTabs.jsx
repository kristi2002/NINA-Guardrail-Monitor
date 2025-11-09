/**
 * Security Tab Navigation Component
 */
import './SecurityTabs.css'

const tabs = [
  { id: 'overview', label: 'Overview', icon: '🛡️' },
  { id: 'threats', label: 'Threats', icon: '⚠️' },
  { id: 'access', label: 'Access Control', icon: '🔐' },
  { id: 'compliance', label: 'Compliance', icon: '📋' },
  { id: 'incidents', label: 'Incidents', icon: '🚨' },
  { id: 'alerting', label: 'Alerting', icon: '📡' }
]

export default function SecurityTabs({ activeTab, onTabClick }) {
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

