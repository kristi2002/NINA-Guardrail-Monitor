/**
 * Analytics Header Component
 */
import { TimeAgo } from '../../../components/ui'
import './AnalyticsHeader.css'

export default function AnalyticsHeader({ timeRange, onTimeRangeChange, onExport, lastUpdated }) {
  const timeRanges = [
    { value: '1d', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ]

  return (
    <div className="analytics-header">
      <div className="header-left">
        <h1>📊 Analytics Dashboard</h1>
        <p className="header-subtitle">
          Comprehensive insights into alert management performance • Last updated: <TimeAgo timestamp={lastUpdated} />
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
        
        <button
          onClick={() => onExport('json')}
          className="export-btn"
        >
          📤 Export
        </button>
      </div>
    </div>
  )
}

