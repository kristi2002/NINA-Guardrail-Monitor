/**
 * Security Header Component
 */
import { TimeAgo } from '../../../components/ui'
import './SecurityHeader.css'

export default function SecurityHeader({ timeRange, onTimeRangeChange, lastUpdated }) {
  const timeRanges = [
    { value: '1d', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ]

  return (
    <div className="security-header">
      <div className="header-left">
        <h1>🛡️ Security Dashboard</h1>
        <p className="header-subtitle">
          Comprehensive security monitoring and threat analysis • Last updated: <TimeAgo timestamp={lastUpdated} />
        </p>
      </div>
      
      <div className="header-controls">
        <select
          value={timeRange}
          onChange={(e) => onTimeRangeChange(e.target.value)}
          className="time-range-select"
        >
          {timeRanges.map(range => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

