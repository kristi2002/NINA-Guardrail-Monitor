/**
 * Security Data Hook
 * Manages data fetching with abort controller and loading states
 */
import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { notificationService } from '../../../services/notifications'

export function useSecurityData(activeTab, timeRange) {
  const [securityData, setSecurityData] = useState(null)
  const [loading, setLoading] = useState(true) // Start with true for initial load
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  
  const prevTimeRange = useRef(timeRange)
  const prevActiveTab = useRef(activeTab)

  const fetchSecurityData = async (showLoadingSpinner = true, signal = null) => {
    try {
      if (showLoadingSpinner) {
        setLoading(true)
      }
      setError(null)

      const config = signal ? { signal } : {}

      // Map tab IDs to endpoints
      const endpointMap = {
        'overview': '/api/security/overview',
        'threats': `/api/security/threats?timeRange=${timeRange}`,
        'access': `/api/security/access?timeRange=${timeRange}`,
        'compliance': '/api/security/compliance',
        'incidents': `/api/security/incidents?timeRange=${timeRange}`,
        'alerting': '/api/security/alerting?limit=20'
      }

      const endpoint = endpointMap[activeTab] || '/api/security/overview'
      const response = await axios.get(endpoint, config)

      // Handle response data structure
      let data = null
      if (response.data.success && response.data.data) {
        data = response.data.data
      } else if (response.data) {
        data = response.data
      }

      if (data) {
        setSecurityData(data)
      } else {
        setSecurityData({})
      }
      setLastUpdated(new Date())
    } catch (err) {
      if (err.name === 'CanceledError' || axios.isCancel(err)) {
        console.log('[SECURITY] Request was cancelled')
        return
      }
      
      if (err.response) {
        setError(`Failed to load ${activeTab} data: ${err.response.status} ${err.response.statusText}`)
      } else if (err.request) {
        setError(`Network error: Unable to connect to server for ${activeTab} data`)
      } else {
        setError(`Failed to load ${activeTab} data: ${err.message}`)
      }
      setSecurityData({})
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    const timeRangeChanged = prevTimeRange.current !== timeRange
    const tabChanged = prevActiveTab.current !== activeTab

    if (timeRangeChanged) {
      fetchSecurityData(true, signal)
    } else if (tabChanged) {
      setSecurityData(null)
      fetchSecurityData(false, signal)
    } else {
      fetchSecurityData(true, signal)
    }

    prevTimeRange.current = timeRange
    prevActiveTab.current = activeTab

    // Auto-refresh interval
    const interval = setInterval(() => {
      console.log('[SECURITY] Auto-refreshing security data...')
      fetchSecurityData(false)
    }, 300000) // 5 minutes

    return () => {
      console.log('🧹 Cleaning up Security: aborting requests...')
      controller.abort()
      clearInterval(interval)
    }
  }, [timeRange, activeTab])

  useEffect(() => {
    let unsubscribeGuardrail = null
    let unsubscribeOperator = null

    const handleRealtimeUpdate = () => {
      fetchSecurityData(false)
    }

    unsubscribeGuardrail = notificationService.subscribe('guardrail_event', handleRealtimeUpdate)
    unsubscribeOperator = notificationService.subscribe('operator_action', handleRealtimeUpdate)

    return () => {
      if (unsubscribeGuardrail) unsubscribeGuardrail()
      if (unsubscribeOperator) unsubscribeOperator()
    }
  }, [activeTab, timeRange])

  return {
    securityData,
    loading,
    error,
    lastUpdated,
    fetchSecurityData
  }
}

