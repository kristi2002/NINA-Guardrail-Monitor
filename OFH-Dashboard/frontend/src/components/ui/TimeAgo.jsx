import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

function TimeAgo({ timestamp }) {
  const [timeString, setTimeString] = useState('')
  const { t } = useTranslation()

  const calculateTimeString = useCallback(() => {
    if (!timestamp) return ''
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000)

    if (seconds < 5) {
      return t('timeAgo.justNow')
    }

    if (seconds < 60) {
      return t('timeAgo.secondsAgo', { count: seconds })
    }

    const minutes = Math.floor(seconds / 60)
    return t('timeAgo.minutesAgo', { count: minutes })
  }, [timestamp, t])

  useEffect(() => {
    // Set the initial value
    setTimeString(calculateTimeString())
    
    // Update it every 5 seconds (1s is overkill)
    const interval = setInterval(() => {
      setTimeString(calculateTimeString())
    }, 5000)

    return () => clearInterval(interval)
  }, [calculateTimeString])

  if (!timeString) {
    return null
  }

  return <span className="last-updated">{t('timeAgo.updated', { time: timeString })}</span>
}

export default TimeAgo
