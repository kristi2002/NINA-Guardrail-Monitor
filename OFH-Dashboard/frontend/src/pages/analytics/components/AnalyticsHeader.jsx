/**
 * Analytics Header Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { TimeAgo } from '../../../components/ui'
import './AnalyticsHeader.css'

export default function AnalyticsHeader({ timeRange, onTimeRangeChange, onExport, lastUpdated, exporting = false, hasData = true }) {
  const { t } = useTranslation()

  const timeRanges = useMemo(() => ([
    { value: '1d', label: t('analytics.header.timeRanges.1d') },
    { value: '7d', label: t('analytics.header.timeRanges.7d') },
    { value: '30d', label: t('analytics.header.timeRanges.30d') }
  ]), [t])

  const exportTitle = !hasData
    ? t('analytics.header.export.tooltip.noData')
    : exporting
      ? t('analytics.header.export.tooltip.exporting')
      : t('analytics.header.export.tooltip.ready')

  return (
    <div className="analytics-header">
      <div className="header-left">
        <h1>{t('analytics.header.title')}</h1>
        <p className="header-subtitle">
          {t('analytics.header.subtitle')} <TimeAgo timestamp={lastUpdated} />
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
          title={exportTitle}
        >
          {exporting ? (
            <>
              <span className="loading-spinner" style={{ display: 'inline-block', width: '12px', height: '12px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.6s linear infinite', marginRight: '6px' }}></span>
              {t('analytics.header.export.exporting')}
            </>
          ) : (
            t('analytics.header.export.button')
          )}
        </button>
      </div>
    </div>
  )
}

