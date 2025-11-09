/**
 * Analytics Data Hook
 * Manages data fetching with abort controller and loading states
 */
import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { notificationService } from '../../../services/notifications'

export function useAnalyticsData(activeTab, timeRange) {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  
  const prevTimeRange = useRef(timeRange)
  const prevActiveTab = useRef(activeTab)
  const isInitialMount = useRef(true)
  const abortControllerRef = useRef(null)
  const requestIdRef = useRef(0)
  const inFlightRequestRef = useRef(null) // Track in-flight requests to prevent duplicates

  const fetchAnalyticsData = async (showLoadingSpinner = true, signal = null) => {
    console.log(`[ANALYTICS] fetchAnalyticsData called - showLoading: ${showLoadingSpinner}, tab: ${activeTab}, timeRange: ${timeRange}`)
    
    // Map tab IDs to endpoint names - define this early so requestKey is always available
    const endpointMap = {
      'overview': 'overview',
      'notifications': 'notifications',
      'users': 'admin-performance',
      'alerts': 'alert-trends',
      'response': 'response-times',
      'escalations': 'escalations',
      'guardrail-performance': 'guardrail-performance'
    }
    
    const endpointName = endpointMap[activeTab] || 'overview'
    const endpoint = `/api/analytics/${endpointName}?timeRange=${timeRange}`
    const requestKey = `${endpointName}-${timeRange}` // Define requestKey early
    
    try {
      if (signal?.aborted) {
        console.log('[ANALYTICS] Request already aborted, skipping fetch')
        return
      }
      
      // Check if there's already an in-flight request for the same endpoint
      if (inFlightRequestRef.current === requestKey) {
        console.log(`[ANALYTICS] Request already in-flight for ${requestKey}, skipping duplicate`)
        return
      }

      // Mark request as in-flight
      inFlightRequestRef.current = requestKey

      if (showLoadingSpinner) {
        setLoading(true)
      }
      setError(null)

      const config = signal ? { signal } : {}
      
      console.log(`[ANALYTICS] Fetching from: ${endpoint}`)
      const response = await axios.get(endpoint, config)
      
      // Handle response data structure
      let data = null
      if (response.data.success && response.data.data) {
        data = response.data.data
      } else if (response.data) {
        data = response.data
      }
      
      // Ensure data has required structure with safe defaults
      const safeData = {
        ...(data || {}),
        alerts: (data && data.alerts) || {},
        conversations: (data && data.conversations) || {},
        users: (data && data.users) || {},
        system_health: (data && data.system_health) || {},
        notification_breakdown: (data && data.notification_breakdown) || [],
        trends: (data && data.trends) || [],
        response_times: (data && data.response_times) || [],
        escalation_trends: (data && data.escalation_trends) || [],
        alert_breakdown: (data && data.alert_breakdown) || [],
        sla_targets: (data && data.sla_targets) || [],
        escalation_reasons: (data && data.escalation_reasons) || [],
        trend_analysis: (data && data.trend_analysis) || { most_common_type: 'N/A', week_over_week_change: 0 },
        peak_hours: (data && data.peak_hours) || { peak_hour: 'N/A', peak_count: 0 },
        severity_distribution: (data && data.severity_distribution) || [],
        failure_reasons: (data && data.failure_reasons) || [],
        supervisor_response: (data && data.supervisor_response) || { avg_supervisor_response_time: 'N/A', supervisor_resolution_rate: 0 },
        escalation_timing: (data && data.escalation_timing) || { fastest_escalation: 'N/A' },
        overall_avg_response_time: (data && data.overall_avg_response_time) || 'N/A',
        sla_compliance_rate: (data && data.sla_compliance_rate) || 0,
        total_escalations: (data && data.total_escalations) || 0,
        auto_escalation_percentage: (data && data.auto_escalation_percentage) || 0,
        escalation_rate: (data && data.escalation_rate) || 0
      }
      
      setAnalyticsData(safeData)
      setLastUpdated(new Date())
      setLoading(false)
      
      // Clear in-flight request on success
      if (inFlightRequestRef.current === requestKey) {
        inFlightRequestRef.current = null
      }
    } catch (err) {
      // Clear in-flight request on error
      if (inFlightRequestRef.current === requestKey) {
        inFlightRequestRef.current = null
      }
      
      if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
        // Handle 429 rate limit errors gracefully
        if (err.response?.status === 429) {
          const retryAfter = err.response?.headers?.['retry-after'] || 5
          console.warn(`[ANALYTICS] Rate limited (429), will retry after ${retryAfter}s`)
          setError(`Too many requests. Please wait ${retryAfter} seconds before refreshing.`)
          
          // Auto-retry after delay if it's a rate limit
          setTimeout(() => {
            if (inFlightRequestRef.current !== requestKey) {
              fetchAnalyticsData(showLoadingSpinner, null)
            }
          }, retryAfter * 1000)
        } else {
          console.error(`[ANALYTICS] Error in fetchAnalyticsData:`, err)
          setError(err.response?.data?.error || err.message || 'Failed to fetch analytics data')
        }
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    const currentRequestId = ++requestIdRef.current
    const isInitial = isInitialMount.current
    
    console.log(`[ANALYTICS] Effect running - Request ID: ${currentRequestId}, Tab: ${activeTab}, TimeRange: ${timeRange}, IsInitial: ${isInitial}`)
    
    const timeRangeChanged = prevTimeRange.current !== timeRange
    const tabChanged = prevActiveTab.current !== activeTab
    
    // Build request key to check for duplicates
    const endpointMap = {
      'overview': 'overview',
      'notifications': 'notifications',
      'users': 'admin-performance',
      'alerts': 'alert-trends',
      'response': 'response-times',
      'escalations': 'escalations'
    }
    const endpointName = endpointMap[activeTab] || 'overview'
    const requestKey = `${endpointName}-${timeRange}`
    
    // Check if we're already fetching this exact endpoint
    if (inFlightRequestRef.current === requestKey) {
      console.log(`[ANALYTICS] Already fetching ${requestKey}, skipping duplicate request`)
      return
    }
    
    const shouldAbortPrevious = !isInitial && (timeRangeChanged || tabChanged)
    
    if (abortControllerRef.current && shouldAbortPrevious) {
      console.log('[ANALYTICS] Aborting previous request due to dependency change')
      abortControllerRef.current.abort()
      inFlightRequestRef.current = null // Clear in-flight ref when aborting
    }

    const controller = new AbortController()
    abortControllerRef.current = controller
    const signal = controller.signal

    prevTimeRange.current = timeRange
    prevActiveTab.current = activeTab

    if (isInitial) {
      console.log('[ANALYTICS] Initial mount - fetching with loader')
      isInitialMount.current = false
      fetchAnalyticsData(true, signal)
    } else if (timeRangeChanged || tabChanged) {
      if (timeRangeChanged) {
        console.log('[ANALYTICS] Time range changed - fetching with loader')
        fetchAnalyticsData(true, signal)
      } else {
        console.log('[ANALYTICS] Tab changed - fetching with skeleton')
        fetchAnalyticsData(false, signal)
      }
    } else {
      // React StrictMode double-invocation: only fetch if we truly have no data
      // and no request is in-flight
      if (!analyticsData && !inFlightRequestRef.current) {
        console.log('[ANALYTICS] No changes but no data - fetching (previous request was likely aborted)')
        fetchAnalyticsData(true, signal)
      } else {
        console.log('[ANALYTICS] No changes detected - skipping fetch (likely React StrictMode double-run)')
      }
    }

    // Auto-refresh interval
    const interval = setInterval(() => {
      // Only auto-refresh if no request is in-flight
      if (!inFlightRequestRef.current) {
        console.log('[ANALYTICS] Auto-refreshing analytics data...')
        fetchAnalyticsData(false)
      } else {
        console.log('[ANALYTICS] Skipping auto-refresh - request already in-flight')
      }
    }, 300000) // 5 minutes

    return () => {
      console.log('🧹 Cleaning up Analytics: aborting requests...')
      controller.abort()
      inFlightRequestRef.current = null // Clear in-flight ref on cleanup
      clearInterval(interval)
    }
  }, [timeRange, activeTab, analyticsData]) // Include analyticsData to properly detect when data exists

  useEffect(() => {
    let unsubscribeGuardrail = null
    let unsubscribeOperator = null

    const handleRealtimeUpdate = () => {
      fetchAnalyticsData(false)
    }

    unsubscribeGuardrail = notificationService.subscribe('guardrail_event', handleRealtimeUpdate)
    unsubscribeOperator = notificationService.subscribe('operator_action', handleRealtimeUpdate)

    return () => {
      if (unsubscribeGuardrail) unsubscribeGuardrail()
      if (unsubscribeOperator) unsubscribeOperator()
    }
  }, [activeTab, timeRange])

  return {
    analyticsData,
    loading,
    error,
    lastUpdated,
    fetchAnalyticsData
  }
}

