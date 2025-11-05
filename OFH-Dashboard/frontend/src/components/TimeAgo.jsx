import { useState, useEffect } from 'react'

function TimeAgo({ timestamp }) {
  const [timeString, setTimeString] = useState('')

  const calculateTimeString = () => {
    if (!timestamp) return ''
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m ago`
  }

  useEffect(() => {
    // Set the initial value
    setTimeString(calculateTimeString())
    
    // Update it every 5 seconds (1s is overkill)
    const interval = setInterval(() => {
      setTimeString(calculateTimeString())
    }, 5000)

    return () => clearInterval(interval)
  }, [timestamp]) // Re-calculate if the timestamp prop changes

  return <span className="last-updated">Updated {timeString}</span>
}

export default TimeAgo
