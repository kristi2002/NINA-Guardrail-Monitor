/**
 * Analytics Header Component
 */
import { TimeAgo } from '../../../components/ui'
import './AnalyticsHeader.css'

export default function AnalyticsHeader({ timeRange, onTimeRangeChange, onExport, lastUpdated, exporting = false, hasData = true }) {
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
          onClick={() => onExport()}
          className="export-btn"
          disabled={exporting || !hasData}
          title={!hasData ? 'No data available to export' : exporting ? 'Exporting...' : 'Export current tab data as JSON'}
        >
          {exporting ? (
            <>
              <span className="loading-spinner" style={{ display: 'inline-block', width: '12px', height: '12px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.6s linear infinite', marginRight: '6px' }}></span>
              Exporting...
            </>
          ) : (
            '📤 Export'
          )}
        </button>
      </div>
    </div>
  )
}

