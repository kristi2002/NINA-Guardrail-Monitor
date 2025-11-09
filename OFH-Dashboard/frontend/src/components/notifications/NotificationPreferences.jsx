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
    notificationsEnabled: true,
    email: {
      enabled: true,
      critical: true,
      warning: true,
      info: false,
      digest: true,
      digestFrequency: 'daily',
      address: ''
    },
    sms: {
      enabled: false,
      critical: true,
      warning: false,
      info: false,
      number: ''
    },
    push: {
      enabled: true,
      critical: true,
      warning: true,
      info: true,
      deviceToken: ''
    },
    webhook: {
      enabled: false,
      url: '',
      critical: true,
      warning: false,
      info: false,
      headers: {}
    },
    escalation: {
      enabled: true,
      autoEscalate: true,
      escalationDelay: 15,
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
  const [success, setSuccess] = useState('')
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    if (isOpen && user) {
      setInitialized(false)
      loadPreferences()
    } else if (!isOpen) {
      setSuccess('')
      setError(null)
    }
  }, [isOpen, user])

  const loadPreferences = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await notificationService.getNotificationPreferences()
      
      if (result.success && result.data) {
        const data = result.data
        const transformedPreferences = {
          notificationsEnabled: data.notificationsEnabled ?? true,
          email: {
            enabled: data.email?.enabled ?? true,
            critical: data.email?.critical ?? true,
            warning: data.email?.warning ?? true,
            info: data.email?.info ?? false,
            digest: data.email?.digest ?? false,
            digestFrequency: data.email?.digestFrequency || 'daily',
            address: data.email?.address || user?.email || ''
          },
          sms: {
            enabled: data.sms?.enabled ?? false,
            critical: data.sms?.critical ?? true,
            warning: data.sms?.warning ?? false,
            info: data.sms?.info ?? false,
            number: data.sms?.number || user?.phone || ''
          },
          push: {
            enabled: data.push?.enabled ?? true,
            critical: data.push?.critical ?? true,
            warning: data.push?.warning ?? true,
            info: data.push?.info ?? true,
            deviceToken: data.push?.deviceToken || ''
          },
          webhook: {
            enabled: data.webhook?.enabled ?? false,
            url: data.webhook?.url || '',
            critical: data.webhook?.critical ?? true,
            warning: data.webhook?.warning ?? false,
            info: data.webhook?.info ?? false,
            headers: data.webhook?.headers || {}
          },
          quietHours: {
            enabled: data.quietHours?.enabled ?? false,
            start: data.quietHours?.start || '22:00',
            end: data.quietHours?.end || '08:00',
            timezone: data.quietHours?.timezone || 'UTC'
          },
          escalation: {
            enabled: data.escalation?.enabled ?? true,
            autoEscalate: data.escalation?.autoEscalate ?? false,
            escalationDelay: Number(data.escalation?.escalationDelay ?? 15),
            maxEscalations: Number(data.escalation?.maxEscalations ?? 3)
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
      setInitialized(true)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess('')

    try {
      const escalationDelay = (() => {
        const value = Number(preferences.escalation?.escalationDelay)
        if (Number.isFinite(value)) {
          return Math.min(1440, Math.max(1, Math.trunc(value)))
        }
        return 15
      })()

      const maxEscalations = (() => {
        const value = Number(preferences.escalation?.maxEscalations)
        if (Number.isFinite(value)) {
          return Math.min(10, Math.max(1, Math.trunc(value)))
        }
        return 3
      })()

      const payload = {
        notificationsEnabled: preferences.notificationsEnabled ?? true,
        email: {
          enabled: !!preferences.email?.enabled,
          critical: !!preferences.email?.critical,
          warning: !!preferences.email?.warning,
          info: !!preferences.email?.info,
          digest: !!preferences.email?.digest,
          digestFrequency: ['hourly', 'daily', 'weekly'].includes(preferences.email?.digestFrequency)
            ? preferences.email.digestFrequency
            : 'daily',
          address: (preferences.email?.address || '').trim()
        },
        sms: {
          enabled: !!preferences.sms?.enabled,
          critical: !!preferences.sms?.critical,
          warning: !!preferences.sms?.warning,
          info: !!preferences.sms?.info,
          number: (preferences.sms?.number || '').trim()
        },
        push: {
          enabled: !!preferences.push?.enabled,
          critical: !!preferences.push?.critical,
          warning: !!preferences.push?.warning,
          info: !!preferences.push?.info,
          deviceToken: (preferences.push?.deviceToken || '').trim()
        },
        webhook: {
          enabled: !!preferences.webhook?.enabled,
          url: (preferences.webhook?.url || '').trim(),
          critical: !!preferences.webhook?.critical,
          warning: !!preferences.webhook?.warning,
          info: !!preferences.webhook?.info,
          headers: preferences.webhook?.headers || {}
        },
        escalation: {
          enabled: !!preferences.escalation?.enabled,
          autoEscalate: !!preferences.escalation?.autoEscalate,
          escalationDelay,
          maxEscalations
        },
        quietHours: {
          enabled: !!preferences.quietHours?.enabled,
          start: preferences.quietHours?.start || '22:00',
          end: preferences.quietHours?.end || '08:00',
          timezone: preferences.quietHours?.timezone || 'UTC'
        }
      }

      const result = await notificationService.updateNotificationPreferences(payload)
      
      if (result.success) {
        setPreferences(prev => ({
          ...prev,
          ...payload,
          email: { ...prev.email, ...payload.email },
          sms: { ...prev.sms, ...payload.sms },
          push: { ...prev.push, ...payload.push },
          webhook: { ...prev.webhook, ...payload.webhook },
          escalation: { ...prev.escalation, ...payload.escalation },
          quietHours: { ...prev.quietHours, ...payload.quietHours }
        }))
        setSuccess('Notification preferences updated successfully.')
        // Close modal after successful save
        setTimeout(() => {
          setSuccess('')
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
    
    const emailTarget = (preferences.email?.address || user?.email || '').trim()
    const smsTarget = (preferences.sms?.number || user?.phone || '').trim()

    if (type === 'email' && !emailTarget) {
      setError('No email address configured for test email notifications.')
      return
    }

    if (type === 'sms' && !smsTarget) {
      setError('No phone number configured for test SMS notifications.')
      return
    }

    try {
      const testNotification = {
        type,
        subject: `Test ${type} notification`,
        message: `This is a test ${type} notification from the system.`,
        priority: 'info',
        recipients: {
          email: type === 'email' ? emailTarget : null,
          sms: type === 'sms' ? smsTarget : null
        }
      }

      console.log('Sending test notification:', testNotification)
      const result = await messagingService.testNotification(testNotification)
      console.log('Test notification result:', result)
      
      if (result.success) {
        setSuccess(`Test ${type} notification sent successfully!`)
        setTimeout(() => setSuccess(''), 5000)
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

  const emailTestTarget = (preferences.email?.address || user?.email || '').trim()
  const smsTestTarget = (preferences.sms?.number || user?.phone || '').trim()

  if (!isOpen) return null

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

        <div className="notification-preferences-body">
          {(loading || !initialized) ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading preferences...</p>
            </div>
          ) : (
            <>
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

              <div className="notification-preferences-content">
                <div className="preference-section">
                  <div className="section-header">
                    <h3>🔔 Global Notifications</h3>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={safeGet(preferences, 'notificationsEnabled', true)}
                        onChange={(e) => updatePreference('notificationsEnabled', e.target.checked)}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                  <p className="section-description">
                    Control whether notifications are delivered at all. When disabled, channel-specific alerts are
                    suppressed until re-enabled.
                  </p>
                </div>

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

                      <div className="input-group">
                        <label>Email Address:</label>
                        <input
                          type="email"
                          value={preferences.email.address}
                          onChange={(e) => updatePreference('email.address', e.target.value)}
                          placeholder={user?.email || 'operator@example.com'}
                        />
                      </div>
                      
                      <button
                        className="test-btn"
                        onClick={() => handleTestNotification('email')}
                        disabled={!emailTestTarget}
                        title={!emailTestTarget ? 'No email address available' : 'Send test email notification'}
                      >
                        {!emailTestTarget ? 'No Email Available' : 'Test Email'}
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

                      <div className="input-group">
                        <label>Phone Number:</label>
                        <input
                          type="tel"
                          value={preferences.sms.number}
                          onChange={(e) => updatePreference('sms.number', e.target.value)}
                          placeholder="+1234567890"
                        />
                      </div>
                      
                      <button
                        className="test-btn"
                        onClick={() => handleTestNotification('sms')}
                        disabled={!smsTestTarget}
                      >
                        {!smsTestTarget ? 'No Phone Available' : 'Test SMS'}
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

                      <div className="input-group">
                        <label>Device Token:</label>
                        <input
                          type="text"
                          value={preferences.push.deviceToken}
                          onChange={(e) => updatePreference('push.deviceToken', e.target.value)}
                          placeholder="Optional device token"
                        />
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
            </>
          )}
        </div>

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
