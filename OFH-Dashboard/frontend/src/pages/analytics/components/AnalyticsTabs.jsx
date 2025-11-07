/**
 * Analytics Tab Navigation Component
 */
import './AnalyticsTabs.css'

const tabs = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'notifications', label: 'Notifications', icon: '📧' },
  { id: 'users', label: 'Admin Performance', icon: '👥' },
  { id: 'alerts', label: 'Alert Trends', icon: '📈' },
  { id: 'response', label: 'Response Times', icon: '⏱️' },
  { id: 'escalations', label: 'Escalations', icon: '⬆️' },
  { id: 'guardrail-performance', label: 'Guardrail Performance', icon: '🛡️' }
]

export default function AnalyticsTabs({ activeTab, onTabClick }) {
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

