// Data Cache Service for Performance Optimization
class DataCache {
  constructor() {
    this.cache = new Map()
    this.cacheTimestamps = new Map()
    this.defaultTTL = 30000 // 30 seconds default TTL
  }

  // Set data in cache with TTL
  set(key, data, ttl = this.defaultTTL) {
    this.cache.set(key, data)
    this.cacheTimestamps.set(key, Date.now() + ttl)
  }

  // Get data from cache if not expired
  get(key) {
    const timestamp = this.cacheTimestamps.get(key)
    if (!timestamp || Date.now() > timestamp) {
      this.cache.delete(key)
      this.cacheTimestamps.delete(key)
      return null
    }
    return this.cache.get(key)
  }

  // Check if data exists and is fresh
  has(key) {
    const timestamp = this.cacheTimestamps.get(key)
    if (!timestamp || Date.now() > timestamp) {
      this.cache.delete(key)
      this.cacheTimestamps.delete(key)
      return false
    }
    return this.cache.has(key)
  }

  // Clear specific cache entry
  delete(key) {
    this.cache.delete(key)
    this.cacheTimestamps.delete(key)
  }

  // Clear all cache
  clear() {
    this.cache.clear()
    this.cacheTimestamps.clear()
  }

  // Get cache size
  size() {
    return this.cache.size
  }

  // Cache keys for different data types
  static KEYS = {
    METRICS: 'metrics',
    ALERTS: 'alerts',
    ANALYTICS_OVERVIEW: 'analytics_overview',
    ANALYTICS_NOTIFICATIONS: 'analytics_notifications',
    ANALYTICS_OPERATORS: 'analytics_operators',
    ANALYTICS_ALERTS: 'analytics_alerts',
    ANALYTICS_RESPONSE: 'analytics_response',
    ANALYTICS_ESCALATIONS: 'analytics_escalations',
  }
}

// Global cache instance
const dataCache = new DataCache()

export default dataCache
export { DataCache }
