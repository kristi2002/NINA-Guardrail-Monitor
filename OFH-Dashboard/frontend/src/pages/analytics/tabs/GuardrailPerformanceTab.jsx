/**
 * Guardrail Performance Tab Component
 * Shows analytics for guardrail performance, false alarm rates, and rule accuracy
 * Optimized for fast rendering with memoization and lazy loading
 */
import { useMemo, useState, useEffect } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import MetricCard from './MetricCard'

// Lazy load charts to improve initial render
const LazyBarChart = BarChart
const LazyPieChart = PieChart

export default function GuardrailPerformanceTab({ data, loading, renderMetricCard }) {
  const [chartsLoaded, setChartsLoaded] = useState(false)
  
  // Use data from the main analytics hook instead of fetching separately
  const guardrailData = data
  const guardrailLoading = loading

  // Load charts after initial render to improve perceived performance
  useEffect(() => {
    if (!guardrailLoading && guardrailData) {
      // Small delay to allow metrics to render first
      const timer = setTimeout(() => {
        setChartsLoaded(true)
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [guardrailLoading, guardrailData])

  // Memoize data processing to avoid recalculating on every render
  const processedData = useMemo(() => {
    if (!guardrailData) return null

    const overview = guardrailData.overview || {}
    const rulePerformance = guardrailData.rule_performance || {}
    const problematicRules = guardrailData.problematic_rules || []
    const thresholdAdjustments = guardrailData.threshold_adjustments || {}

    // Prepare data for charts (memoized)
    const ruleAccuracyData = Object.values(rulePerformance).map(rule => ({
      name: rule.rule_name || 'Unknown',
      accuracy: Math.round((rule.accuracy || 0) * 100),
      falseAlarmRate: Math.round((rule.false_alarm_rate || 0) * 100),
      totalDetections: rule.total_detections || 0
    })).sort((a, b) => b.falseAlarmRate - a.falseAlarmRate)

    const thresholdData = Object.entries(thresholdAdjustments).map(([validator, multiplier]) => ({
      name: validator.toUpperCase(),
      multiplier: Math.round((multiplier - 1.0) * 100),
      value: multiplier
    }))

    const falseAlarmTrend = problematicRules.slice(0, 10).map(rule => ({
      name: rule.rule_name || 'Unknown',
      falseAlarmRate: Math.round((rule.false_alarm_rate || 0) * 100),
      totalDetections: rule.total_detections || 0
    }))

    return {
      overview,
      ruleAccuracyData,
      thresholdData,
      falseAlarmTrend,
      problematicRules
    }
  }, [guardrailData])

  // Memoize metric cards data
  const metricsData = useMemo(() => {
    if (!processedData) return []
    
    const { overview, problematicRules } = processedData
    
    return [
      {
        title: 'Total Feedback',
        value: overview.total_feedback || 0,
        description: 'False alarms + True positives',
        icon: '📊'
      },
      {
        title: 'False Alarm Rate',
        value: `${Math.round((overview.false_alarm_rate || 0) * 100)}%`,
        description: 'Lower is better',
        icon: '⚠️'
      },
      {
        title: 'Overall Accuracy',
        value: `${Math.round((overview.accuracy || 0) * 100)}%`,
        description: 'Based on feedback',
        icon: '✅'
      },
      {
        title: 'Rules Tracked',
        value: overview.rules_tracked || 0,
        description: 'Active guardrail rules',
        icon: '🔍'
      },
      {
        title: 'Problematic Rules',
        value: problematicRules.length,
        description: 'High false alarm rate',
        icon: '🚨'
      },
      {
        title: 'True Positives',
        value: overview.true_positives || 0,
        description: 'Confirmed valid detections',
        icon: '✓'
      }
    ]
  }, [processedData])

  if (guardrailLoading) {
    return (
      <div className="analytics-tab-skeleton">
        <div className="skeleton-metric-grid">
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton-card"></div>)}
        </div>
        <div className="skeleton-chart-grid">
          <div className="skeleton-chart"></div>
          <div className="skeleton-chart"></div>
        </div>
      </div>
    )
  }

  // Check if data is available - handle both direct data and wrapped data structures
  const isAvailable = guardrailData && (
    guardrailData.available === true || 
    (guardrailData.overview !== undefined && guardrailData.available !== false)
  )

  if (!guardrailData || !isAvailable) {
    return (
      <div className="analytics-tab">
        <div className="analytics-loading">
          <p>Guardrail performance analytics not available.</p>
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            {guardrailData?.message || 'Adaptive learning may not be enabled in Guardrail Strategy service.'}
          </p>
        </div>
      </div>
    )
  }

  if (!processedData) {
    return (
      <div className="analytics-tab">
        <div className="analytics-loading">
          <p>Processing data...</p>
        </div>
      </div>
    )
  }

  const { overview, ruleAccuracyData, thresholdData, falseAlarmTrend, problematicRules } = processedData

  return (
    <div className="analytics-tab">
      {/* Render metrics first (fast rendering) */}
      <div className="metrics-grid">
        {metricsData.map((metric, index) => (
          <div key={`metric-${index}`}>
            {renderMetricCard(
              metric.title,
              metric.value,
              metric.description,
              metric.icon
            )}
          </div>
        ))}
      </div>

      {/* Lazy load charts after metrics render */}
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Rule Accuracy vs False Alarm Rate</h3>
          {chartsLoaded && ruleAccuracyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LazyBarChart data={ruleAccuracyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="accuracy" fill="#4caf50" name="Accuracy %" />
                <Bar dataKey="falseAlarmRate" fill="#f97316" name="False Alarm Rate %" />
              </LazyBarChart>
            </ResponsiveContainer>
          ) : chartsLoaded ? (
            <div className="chart-placeholder">No rule performance data available</div>
          ) : (
            <div className="chart-placeholder">Loading chart...</div>
          )}
        </div>

        <div className="chart-container">
          <h3>Threshold Adjustments</h3>
          {chartsLoaded && thresholdData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LazyBarChart data={thresholdData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Adjustment %', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `${value > 0 ? '+' : ''}${value}%`} />
                <Bar dataKey="multiplier" fill="#2196f3" name="Threshold Adjustment %" />
              </LazyBarChart>
            </ResponsiveContainer>
          ) : chartsLoaded ? (
            <div className="chart-placeholder">No threshold adjustments yet</div>
          ) : (
            <div className="chart-placeholder">Loading chart...</div>
          )}
        </div>

        <div className="chart-container">
          <h3>Top Problematic Rules (False Alarm Rate)</h3>
          {chartsLoaded && falseAlarmTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LazyBarChart data={falseAlarmTrend} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis dataKey="name" type="category" width={150} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="falseAlarmRate" fill="#dc2626" name="False Alarm Rate %" />
              </LazyBarChart>
            </ResponsiveContainer>
          ) : chartsLoaded ? (
            <div className="chart-placeholder">No problematic rules identified</div>
          ) : (
            <div className="chart-placeholder">Loading chart...</div>
          )}
        </div>

        <div className="chart-container">
          <h3>Feedback Distribution</h3>
          {chartsLoaded && overview.total_feedback > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LazyPieChart>
                <Pie
                  data={[
                    { name: 'False Alarms', value: overview.false_alarms || 0 },
                    { name: 'True Positives', value: overview.true_positives || 0 }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({name, value, percent}) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                >
                  <Cell fill="#f97316" />
                  <Cell fill="#4caf50" />
                </Pie>
                <Tooltip />
              </LazyPieChart>
            </ResponsiveContainer>
          ) : chartsLoaded ? (
            <div className="chart-placeholder">No feedback data available</div>
          ) : (
            <div className="chart-placeholder">Loading chart...</div>
          )}
        </div>
      </div>

      {problematicRules.length > 0 && (
        <div className="problematic-rules-section" style={{ marginTop: '2rem' }}>
          <h3>⚠️ Rules Requiring Attention</h3>
          <div className="rules-list" style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
            {problematicRules.slice(0, 5).map((rule, index) => (
              <div key={index} className="rule-card" style={{
                padding: '1rem',
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{rule.rule_name}</strong>
                    <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
                      False Alarm Rate: {Math.round(rule.false_alarm_rate * 100)}% | 
                      Accuracy: {Math.round((1 - rule.false_alarm_rate) * 100)}% | 
                      Total Detections: {rule.total_detections}
                    </div>
                  </div>
                  <div style={{
                    padding: '0.5rem 1rem',
                    background: rule.false_alarm_rate > 0.5 ? '#fee' : '#fff4e6',
                    borderRadius: '4px',
                    color: rule.false_alarm_rate > 0.5 ? '#c33' : '#f97316',
                    fontWeight: 'bold'
                  }}>
                    {rule.false_alarm_rate > 0.5 ? 'CRITICAL' : 'HIGH'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

