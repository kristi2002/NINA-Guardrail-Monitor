/**
 * Export analytics data utility
 * Updated to support tab-specific exports with client-side data
 */
import axios from 'axios'

export async function exportAnalyticsData(activeTab, timeRange, format = 'json', clientData = null) {
  try {
    // Map tab names for better filenames
    const tabNameMap = {
      'overview': 'overview',
      'notifications': 'notifications',
      'users': 'admin-performance',
      'alerts': 'alert-trends',
      'response': 'response-times',
      'escalations': 'escalations',
      'guardrail-performance': 'guardrail-performance'
    }
    
    const tabLabel = tabNameMap[activeTab] || activeTab || 'overview'
    
    // If we have client data, use it directly for faster export
    // Otherwise, fetch from backend
    let exportData = null
    
    if (clientData && format === 'json') {
      // Use client-side data for immediate export (faster, no API call needed)
      exportData = {
        exported_by: 'current_user', // Will be set by backend if needed
        exported_at: new Date().toISOString(),
        format: format,
        time_range: timeRange,
        tab: activeTab,
        tab_label: tabLabel,
        data: clientData
      }
    } else {
      // Fetch from backend (for server-side processing or when client data unavailable)
      const response = await axios.post('/api/analytics/export', {
        activeTab: activeTab,
        timeRange: timeRange,
        format: format
      })
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Export failed')
      }
      
      exportData = response.data.data
    }
    
    if (format === 'json') {
      const dataStr = JSON.stringify(exportData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      const filename = `analytics-${tabLabel}-${timeRange}-${new Date().toISOString().split('T')[0]}.json`
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      console.log(`✅ Exported analytics data: ${filename}`)
    } else if (format === 'csv') {
      // Convert to CSV (basic implementation)
      const csv = convertToCSV(exportData.data)
      const csvBlob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(csvBlob)
      const link = document.createElement('a')
      const filename = `analytics-${tabLabel}-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      console.log(`✅ Exported analytics data: ${filename}`)
    }
    
    return true
  } catch (error) {
    console.error('Export error:', error)
    alert(`Failed to export data: ${error.message || 'Unknown error'}`)
    return false
  }
}

/**
 * Convert data to CSV format (basic implementation)
 */
function convertToCSV(data) {
  if (!data || typeof data !== 'object') {
    return 'No data available'
  }
  
  // Flatten the data structure for CSV
  const rows = []
  
  // Add header
  if (data.overview) {
    rows.push(['Metric', 'Value'])
    Object.entries(data.overview).forEach(([key, value]) => {
      rows.push([key, String(value)])
    })
  }
  
  // Convert to CSV string
  return rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')
}

