import { useState, useEffect } from 'react'
import { messagingService } from '../../services/api'
import { notificationService } from '../../services/notifications'
import './NotificationPreferences.css'

function NotificationPreferences({ isOpen, onClose, user }) {
  // Helper function to safely access nested properties
  const safeGet = (obj, path, defaultValue = false) => {
    try {
      return path.split('.').reduce((current, key) => {
        return current && current[key] !== undefined ? current[key] : defaultValue
      }, obj)
    } catch (error) {
      console.warn(`Error accessing path ${path}:`, error)
      return defaultValue
    }
  }

  const [preferences, setPreferences] = useState({
    email: {
      enabled: true,
      critical: true,
      warning: true,
      info: false,
      digest: true,
      digestFrequency: 'daily'
    },
    sms: {
      enabled: false,
      critical: true,
      warning: false,
      info: false
    },
    push: {
      enabled: true,
      critical: true,
      warning: true,
      info: true
    },
    webhook: {
      enabled: false,
      url: '',
      critical: true,
      warning: false,
      info: false
    },
    escalation: {
      enabled: true,
      autoEscalate: true,
      escalationDelay: 15, // minutes
      maxEscalations: 3
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
      timezone: 'UTC'
    }
  })

  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (isOpen && user) {
      loadPreferences()
    }
  }, [isOpen, user])

  const loadPreferences = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await notificationService.getNotificationPreferences()
      
      if (result.success && result.data) {
        // Transform backend data structure to match frontend expectations
        const transformedPreferences = {
          email: {
            enabled: result.data.email_notifications || false,
            critical: result.data.alert_types?.critical_alerts || true,
            warning: result.data.alert_types?.warning_alerts || true,
            info: result.data.alert_types?.info_alerts || false,
            digest: result.data.digest_notifications || false,
            digestFrequency: result.data.notification_frequency === 'daily' ? 'daily' : 'weekly',
            address: result.data.channels?.email?.address || ''
          },
          sms: {
            enabled: result.data.channels?.sms?.enabled || false,
            critical: result.data.alert_types?.critical_alerts || true,
            warning: result.data.alert_types?.warning_alerts || false,
            info: result.data.alert_types?.info_alerts || false,
            number: result.data.channels?.sms?.number || ''
          },
          push: {
            enabled: result.data.push_notifications || false,
            critical: result.data.alert_types?.critical_alerts || true,
            warning: result.data.alert_types?.warning_alerts || true,
            info: result.data.alert_types?.info_alerts || true,
            deviceToken: result.data.channels?.push?.device_token || ''
          },
          webhook: {
            enabled: false, // Not in backend data
            url: '',
            headers: {}
          },
          quietHours: {
            enabled: result.data.quiet_hours?.enabled || false,
            start: result.data.quiet_hours?.start || '22:00',
            end: result.data.quiet_hours?.end || '08:00'
          },
          escalation: {
            enabled: result.data.escalation_notifications || false
          }
        }
        setPreferences(transformedPreferences)
        console.log('Preferences loaded and transformed from backend:', transformedPreferences)
      } else {
        console.log('Using default preferences')
      }
    } catch (err) {
      console.error('Failed to load preferences:', err)
      setError('Failed to load notification preferences')
      // Keep default preferences if loading fails
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      const result = await notificationService.updateNotificationPreferences(preferences)
      
      if (result.success) {
        setSuccess(true)
        // Close modal after successful save
        setTimeout(() => {
          setSuccess(false)
          onClose()
        }, 1500) // Show success message for 1.5 seconds before closing
      } else {
        setError(result.error || 'Failed to save notification preferences')
      }
    } catch (err) {
      console.error('Failed to save preferences:', err)
      setError('Failed to save notification preferences')
    } finally {
      setSaving(false)
    }
  }

  const handleTestNotification = async (type) => {
    console.log('Test notification clicked:', type)
    console.log('User object:', user)
    console.log('User email:', user?.email)
    
    try {
      const testNotification = {
        type,
        subject: `Test ${type} notification`,
        message: `This is a test ${type} notification from the system.`,
        priority: 'info',
        recipients: {
          email: type === 'email' ? user?.email : null,
          sms: type === 'sms' ? user?.phone : null
        }
      }

      console.log('Sending test notification:', testNotification)
      const result = await messagingService.testNotification(testNotification)
      console.log('Test notification result:', result)
      
      if (result.success) {
        setSuccess(`Test ${type} notification sent successfully!`)
        setTimeout(() => setSuccess(false), 5000)
      } else {
        setError(`Failed to send test ${type} notification: ${result.error}`)
      }
    } catch (err) {
      console.error('Test notification failed:', err)
      setError(`Failed to send test ${type} notification`)
    }
  }

  const updatePreference = (path, value) => {
    setPreferences(prev => {
      const newPrefs = { ...prev }
      const keys = path.split('.')
      let current = newPrefs
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]]
      }
      
      current[keys[keys.length - 1]] = value
      return newPrefs
    })
  }

  if (!isOpen) return null

  // Show loading state while preferences are being loaded
  if (loading) {
    return (
      <div className="notification-preferences-overlay">
        <div className="notification-preferences">
          <div className="notification-preferences-header">
            <h2>🔔 Notification Preferences</h2>
            <button 
              className="close-btn"
              onClick={onClose}
              aria-label="Close"
            >
              ×
            </button>
          </div>
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading preferences...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="notification-preferences-overlay">
      <div className="notification-preferences-modal">
        <div className="notification-preferences-header">
          <h2>🔔 Notification Preferences</h2>
          <button 
            className="close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {loading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading preferences...</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            <span className="success-icon">✅</span>
            {success}
          </div>
        )}

        {!loading && (
          <div className="notification-preferences-content">
            {/* Email Notifications */}
            <div className="preference-section">
              <div className="section-header">
                <h3>📧 Email Notifications</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={preferences.email?.enabled || false}
                    onChange={(e) => updatePreference('email.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {preferences.email?.enabled && (
                <div className="preference-options">
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={safeGet(preferences, 'email.critical', false)}
                        onChange={(e) => updatePreference('email.critical', e.target.checked)}
                      />
                      Critical Alerts
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={safeGet(preferences, 'email.warning', false)}
                        onChange={(e) => updatePreference('email.warning', e.target.checked)}
                      />
                      Warning Alerts
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={safeGet(preferences, 'email.info', false)}
                        onChange={(e) => updatePreference('email.info', e.target.checked)}
                      />
                      Info Alerts
                    </label>
                  </div>
                  
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={safeGet(preferences, 'email.digest', false)}
                        onChange={(e) => updatePreference('email.digest', e.target.checked)}
                      />
                      Daily Digest
                    </label>
                    
                    {safeGet(preferences, 'email.digest', false) && (
                      <select
                        value={safeGet(preferences, 'email.digestFrequency', 'daily')}
                        onChange={(e) => updatePreference('email.digestFrequency', e.target.value)}
                      >
                        <option value="hourly">Hourly</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                      </select>
                    )}
                  </div>
                  
                  <button
                    className="test-btn"
                    onClick={() => handleTestNotification('email')}
                    disabled={!user?.email}
                    title={!user?.email ? 'No email address available' : 'Send test email notification'}
                  >
                    {!user?.email ? 'No Email Available' : 'Test Email'}
                  </button>
                </div>
              )}
            </div>

            {/* SMS Notifications */}
            <div className="preference-section">
              <div className="section-header">
                <h3>📱 SMS Notifications</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={safeGet(preferences, 'sms.enabled', false)}
                    onChange={(e) => updatePreference('sms.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {safeGet(preferences, 'sms.enabled', false) && (
                <div className="preference-options">
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.sms.critical}
                        onChange={(e) => updatePreference('sms.critical', e.target.checked)}
                      />
                      Critical Alerts Only
                    </label>
                  </div>
                  
                  <button
                    className="test-btn"
                    onClick={() => handleTestNotification('sms')}
                    disabled={!user?.phone}
                  >
                    Test SMS
                  </button>
                </div>
              )}
            </div>

            {/* Push Notifications */}
            <div className="preference-section">
              <div className="section-header">
                <h3>🔔 Push Notifications</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={safeGet(preferences, 'push.enabled', false)}
                    onChange={(e) => updatePreference('push.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {safeGet(preferences, 'push.enabled', false) && (
                <div className="preference-options">
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.push.critical}
                        onChange={(e) => updatePreference('push.critical', e.target.checked)}
                      />
                      Critical Alerts
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.push.warning}
                        onChange={(e) => updatePreference('push.warning', e.target.checked)}
                      />
                      Warning Alerts
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.push.info}
                        onChange={(e) => updatePreference('push.info', e.target.checked)}
                      />
                      Info Alerts
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Webhook Notifications */}
            <div className="preference-section">
              <div className="section-header">
                <h3>🔗 Webhook Notifications</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={safeGet(preferences, 'webhook.enabled', false)}
                    onChange={(e) => updatePreference('webhook.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {safeGet(preferences, 'webhook.enabled', false) && (
                <div className="preference-options">
                  <div className="input-group">
                    <label>Webhook URL:</label>
                    <input
                      type="url"
                      value={preferences.webhook.url}
                      onChange={(e) => updatePreference('webhook.url', e.target.value)}
                      placeholder="https://your-webhook-url.com"
                    />
                  </div>
                  
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.webhook.critical}
                        onChange={(e) => updatePreference('webhook.critical', e.target.checked)}
                      />
                      Critical Alerts Only
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Escalation Settings */}
            <div className="preference-section">
              <div className="section-header">
                <h3>🚨 Escalation Settings</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={preferences.escalation.enabled}
                    onChange={(e) => updatePreference('escalation.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {preferences.escalation.enabled && (
                <div className="preference-options">
                  <div className="option-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={preferences.escalation.autoEscalate}
                        onChange={(e) => updatePreference('escalation.autoEscalate', e.target.checked)}
                      />
                      Auto-escalate unresolved alerts
                    </label>
                  </div>
                  
                  <div className="input-group">
                    <label>Escalation Delay (minutes):</label>
                    <div className="number-input-wrapper">
                      <input
                        type="number"
                        min="1"
                        max="1440"
                        value={preferences.escalation.escalationDelay}
                        onChange={(e) => updatePreference('escalation.escalationDelay', parseInt(e.target.value))}
                        onKeyDown={(e) => {
                          if (e.key === 'ArrowUp') {
                            e.preventDefault();
                            const newValue = Math.min(1440, preferences.escalation.escalationDelay + 1);
                            updatePreference('escalation.escalationDelay', newValue);
                          } else if (e.key === 'ArrowDown') {
                            e.preventDefault();
                            const newValue = Math.max(1, preferences.escalation.escalationDelay - 1);
                            updatePreference('escalation.escalationDelay', newValue);
                          }
                        }}
                      />
                      <div className="number-input-buttons">
                        <button
                          type="button"
                          className="number-input-up"
                          onClick={() => {
                            const newValue = Math.min(1440, preferences.escalation.escalationDelay + 1);
                            updatePreference('escalation.escalationDelay', newValue);
                          }}
                        >
                          ▲
                        </button>
                        <button
                          type="button"
                          className="number-input-down"
                          onClick={() => {
                            const newValue = Math.max(1, preferences.escalation.escalationDelay - 1);
                            updatePreference('escalation.escalationDelay', newValue);
                          }}
                        >
                          ▼
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="input-group">
                    <label>Max Escalations:</label>
                    <div className="number-input-wrapper">
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={preferences.escalation.maxEscalations}
                        onChange={(e) => updatePreference('escalation.maxEscalations', parseInt(e.target.value))}
                        onKeyDown={(e) => {
                          if (e.key === 'ArrowUp') {
                            e.preventDefault();
                            const newValue = Math.min(10, preferences.escalation.maxEscalations + 1);
                            updatePreference('escalation.maxEscalations', newValue);
                          } else if (e.key === 'ArrowDown') {
                            e.preventDefault();
                            const newValue = Math.max(1, preferences.escalation.maxEscalations - 1);
                            updatePreference('escalation.maxEscalations', newValue);
                          }
                        }}
                      />
                      <div className="number-input-buttons">
                        <button
                          type="button"
                          className="number-input-up"
                          onClick={() => {
                            const newValue = Math.min(10, preferences.escalation.maxEscalations + 1);
                            updatePreference('escalation.maxEscalations', newValue);
                          }}
                        >
                          ▲
                        </button>
                        <button
                          type="button"
                          className="number-input-down"
                          onClick={() => {
                            const newValue = Math.max(1, preferences.escalation.maxEscalations - 1);
                            updatePreference('escalation.maxEscalations', newValue);
                          }}
                        >
                          ▼
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quiet Hours */}
            <div className="preference-section">
              <div className="section-header">
                <h3>🌙 Quiet Hours</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={preferences.quietHours.enabled}
                    onChange={(e) => updatePreference('quietHours.enabled', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              
              {preferences.quietHours.enabled && (
                <div className="preference-options">
                  <div className="input-group">
                    <label>Start Time:</label>
                    <input
                      type="time"
                      value={preferences.quietHours.start}
                      onChange={(e) => updatePreference('quietHours.start', e.target.value)}
                    />
                  </div>
                  
                  <div className="input-group">
                    <label>End Time:</label>
                    <input
                      type="time"
                      value={preferences.quietHours.end}
                      onChange={(e) => updatePreference('quietHours.end', e.target.value)}
                    />
                  </div>
                  
                  <div className="input-group">
                    <label>Timezone:</label>
                    <select
                      value={preferences.quietHours.timezone}
                      onChange={(e) => updatePreference('quietHours.timezone', e.target.value)}
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Europe/Paris">Paris</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="notification-preferences-footer">
          <button
            className="cancel-btn"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotificationPreferences
