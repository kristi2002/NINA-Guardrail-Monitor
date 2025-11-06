import axios from 'axios'
import dataCache, { DataCache } from './dataCache'

class DataService {
  constructor() {
    this.baseURL = '/api'
  }

  // Optimized metrics fetching with cache
  async getMetrics(forceRefresh = false) {
    const cacheKey = DataCache.KEYS.METRICS
    
    // Return cached data if available and not forcing refresh
    if (!forceRefresh && dataCache.has(cacheKey)) {
      console.log('📦 Returning cached metrics data')
      return dataCache.get(cacheKey)
    }

    try {
      console.log('🌐 Fetching fresh metrics data')
      const response = await axios.get(`${this.baseURL}/metrics`)
      const data = response.data
      
      // Cache for 15 seconds (metrics update frequently)
      dataCache.set(cacheKey, data, 15000)
      
      return data
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
      throw error
    }
  }

  // Optimized alerts fetching with cache
  async getAlerts(forceRefresh = false) {
    const cacheKey = DataCache.KEYS.ALERTS
    
    if (!forceRefresh && dataCache.has(cacheKey)) {
      console.log('📦 Returning cached alerts data')
      return dataCache.get(cacheKey)
    }

    try {
      console.log('🌐 Fetching fresh alerts data')
      const response = await axios.get(`${this.baseURL}/alerts`)
      const data = response.data
      
      // Cache for 10 seconds (alerts change frequently)
      dataCache.set(cacheKey, data, 10000)
      
      return data
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      throw error
    }
  }

  // Optimized analytics fetching with cache
  async getAnalyticsData(tab, timeRange = '24h', forceRefresh = false) {
    const cacheKey = `${DataCache.KEYS.ANALYTICS_OVERVIEW}_${tab}_${timeRange}`
    
    if (!forceRefresh && dataCache.has(cacheKey)) {
      console.log(`📦 Returning cached analytics data for ${tab}`)
      return dataCache.get(cacheKey)
    }

    try {
      console.log(`🌐 Fetching fresh analytics data for ${tab}`)
      const response = await axios.get(`${this.baseURL}/analytics/${tab}?timeRange=${timeRange}`)
      const data = response.data
      
      // Cache for 2 minutes (analytics don't change as frequently)
      dataCache.set(cacheKey, data, 120000)
      
      return data
    } catch (error) {
      console.error(`Failed to fetch analytics data for ${tab}:`, error)
      throw error
    }
  }

  // Preload critical data
  async preloadCriticalData() {
    console.log('🚀 Preloading critical data...')
    
    try {
      // Load metrics and alerts in parallel
      const [metrics, alerts] = await Promise.allSettled([
        this.getMetrics(),
        this.getAlerts()
      ])

      console.log('✅ Critical data preloaded successfully')
      return {
        metrics: metrics.status === 'fulfilled' ? metrics.value : null,
        alerts: alerts.status === 'fulfilled' ? alerts.value : null,
        errors: {
          metrics: metrics.status === 'rejected' ? metrics.reason : null,
          alerts: alerts.status === 'rejected' ? alerts.reason : null
        }
      }
    } catch (error) {
      console.error('Failed to preload critical data:', error)
      throw error
    }
  }

  // Clear cache for specific data type
  clearCache(dataType) {
    const cacheKey = DataCache.KEYS[dataType.toUpperCase()]
    if (cacheKey) {
      dataCache.delete(cacheKey)
      console.log(`🗑️ Cleared cache for ${dataType}`)
    }
  }

  // Clear all cache
  clearAllCache() {
    dataCache.clear()
    console.log('🗑️ Cleared all cache')
  }

  // Get cache statistics
  getCacheStats() {
    return {
      size: dataCache.size(),
      keys: Array.from(dataCache.cache.keys())
    }
  }
}

// Global data service instance
const dataService = new DataService()

export default dataService
