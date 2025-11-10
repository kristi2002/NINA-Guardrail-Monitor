/**
 * Security Header Component
 */
import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { TimeAgo } from '../../../components/ui'
import './SecurityHeader.css'

export default function SecurityHeader({ timeRange, onTimeRangeChange, lastUpdated }) {
  const { t } = useTranslation()

  const timeRanges = useMemo(() => ([
    { value: '1d', label: t('security.header.timeRanges.1d') },
    { value: '7d', label: t('security.header.timeRanges.7d') },
    { value: '30d', label: t('security.header.timeRanges.30d') }
  ]), [t])

  return (
    <div className="security-header">
      <div className="header-left">
        <h1>{t('security.header.title')}</h1>
        <p className="header-subtitle">
          {t('security.header.subtitle')} <TimeAgo timestamp={lastUpdated} />
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

