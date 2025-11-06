/**
 * Export analytics data utility
 */
import axios from 'axios'

export async function exportAnalyticsData(timeRange, format = 'json') {
  try {
    const response = await axios.post('/api/analytics/export', {
      timeRange: timeRange,
      format: format
    })
    
    if (format === 'json') {
      const dataStr = JSON.stringify(response.data.data, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`
      link.click()
      URL.revokeObjectURL(url)
    }
    
    alert(`Analytics data exported successfully!`)
    return true
  } catch (error) {
    console.error('Export error:', error)
    alert('Failed to export data')
    return false
  }
}

