import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { messagingService } from '../../services/api'
import { notificationService } from '../../services/notifications'
import './NotificationPreferences.css'

const TIMEZONE_VALUES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo'
]

function NotificationPreferences({ isOpen, onClose, user }) {
  const { t } = useTranslation()

  const digestOptions = useMemo(
    () => [
      { value: 'hourly', label: t('notificationPreferences.email.frequencyOptions.hourly') },
      { value: 'daily', label: t('notificationPreferences.email.frequencyOptions.daily') },
      { value: 'weekly', label: t('notificationPreferences.email.frequencyOptions.weekly') }
    ],
    [t]
  )

  const timezoneOptions = useMemo(
    () =>
      TIMEZONE_VALUES.map((zone) => ({
        value: zone,
        label: t(
          `notificationPreferences.quietHours.timezoneOptions.${zone.replace(/\//g, '_')}`,
          { defaultValue: zone }
        )
      })),
    [t]
  )

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
      setError(t('notificationPreferences.messages.loadError'))
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
        setSuccess(t('notificationPreferences.messages.updateSuccess'))
        // Close modal after successful save
        setTimeout(() => {
          setSuccess('')
          onClose()
        }, 1500) // Show success message for 1.5 seconds before closing
      } else {
        setError(result.error || t('notificationPreferences.messages.saveError'))
      }
    } catch (err) {
      console.error('Failed to save preferences:', err)
      setError(t('notificationPreferences.messages.saveError'))
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

    const typeLabel = t(`notificationPreferences.testTypes.${type}`, { defaultValue: type })

    if (type === 'email' && !emailTarget) {
      setError(t('notificationPreferences.messages.testEmailMissing'))
      return
    }

    if (type === 'sms' && !smsTarget) {
      setError(t('notificationPreferences.messages.testSmsMissing'))
      return
    }

    try {
      const testNotification = {
        type,
        subject: t('notificationPreferences.messages.testSubject', { type: typeLabel }),
        message: t('notificationPreferences.messages.testMessage', { type: typeLabel }),
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
        setSuccess(t('notificationPreferences.messages.testSuccess', { type: typeLabel }))
        setTimeout(() => setSuccess(''), 5000)
      } else {
        setError(result.error || t('notificationPreferences.messages.testError', { type: typeLabel }))
      }
    } catch (err) {
      console.error('Test notification failed:', err)
      setError(t('notificationPreferences.messages.testError', { type: typeLabel }))
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
          <h2>🔔 {t('notificationPreferences.title')}</h2>
          <button 
            className="close-btn"
            onClick={onClose}
            aria-label={t('notificationPreferences.actions.close')}
          >
            ×
          </button>
        </div>

        <div className="notification-preferences-body">
          {(loading || !initialized) ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>{t('notificationPreferences.loading')}</p>
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
                    <h3>🔔 {t('notificationPreferences.global.title')}</h3>
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
                    {t('notificationPreferences.global.description')}
                  </p>
                </div>

                {/* Email Notifications */}
                <div className="preference-section">
                  <div className="section-header">
                    <h3>📧 {t('notificationPreferences.email.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.email.description')}
                      </p>
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={safeGet(preferences, 'email.critical', false)}
                            onChange={(e) => updatePreference('email.critical', e.target.checked)}
                          />
                          {t('notificationPreferences.email.toggles.critical')}
                        </label>
                        <label>
                          <input
                            type="checkbox"
                            checked={safeGet(preferences, 'email.warning', false)}
                            onChange={(e) => updatePreference('email.warning', e.target.checked)}
                          />
                          {t('notificationPreferences.email.toggles.warning')}
                        </label>
                        <label>
                          <input
                            type="checkbox"
                            checked={safeGet(preferences, 'email.info', false)}
                            onChange={(e) => updatePreference('email.info', e.target.checked)}
                          />
                          {t('notificationPreferences.email.toggles.info')}
                        </label>
                      </div>
                      
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={safeGet(preferences, 'email.digest', false)}
                            onChange={(e) => updatePreference('email.digest', e.target.checked)}
                          />
                          {t('notificationPreferences.email.digestLabel')}
                        </label>
                        
                        {safeGet(preferences, 'email.digest', false) && (
                          <select
                            value={safeGet(preferences, 'email.digestFrequency', 'daily')}
                            onChange={(e) => updatePreference('email.digestFrequency', e.target.value)}
                            aria-label={t('notificationPreferences.email.frequencyLabel')}
                          >
                            {digestOptions.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>

                      <div className="input-group">
                        <label>{t('notificationPreferences.email.addressLabel')}</label>
                        <input
                          type="email"
                          value={preferences.email.address}
                          onChange={(e) => updatePreference('email.address', e.target.value)}
                          placeholder={user?.email || t('notificationPreferences.email.placeholders.address')}
                        />
                      </div>
                      
                      <button
                        className="test-btn"
                        onClick={() => handleTestNotification('email')}
                        disabled={!emailTestTarget}
                        title={emailTestTarget ? t('notificationPreferences.actions.testEmailTooltip') : t('notificationPreferences.messages.testEmailMissing')}
                      >
                        {emailTestTarget ? t('notificationPreferences.actions.testEmail') : t('notificationPreferences.actions.testEmailDisabled')}
                      </button>
                    </div>
                  )}
                </div>

                {/* SMS Notifications */}
                <div className="preference-section">
                  <div className="section-header">
                    <h3>📱 {t('notificationPreferences.sms.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.sms.description')}
                      </p>
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.sms.critical}
                            onChange={(e) => updatePreference('sms.critical', e.target.checked)}
                          />
                          {t('notificationPreferences.sms.toggles.critical')}
                        </label>
                      </div>

                      <div className="input-group">
                        <label>{t('notificationPreferences.sms.numberLabel')}</label>
                        <input
                          type="tel"
                          value={preferences.sms.number}
                          onChange={(e) => updatePreference('sms.number', e.target.value)}
                          placeholder={t('notificationPreferences.sms.placeholders.number')}
                        />
                      </div>
                      
                      <button
                        className="test-btn"
                        onClick={() => handleTestNotification('sms')}
                        disabled={!smsTestTarget}
                        title={smsTestTarget ? t('notificationPreferences.actions.testSmsTooltip') : t('notificationPreferences.messages.testSmsMissing')}
                      >
                        {smsTestTarget ? t('notificationPreferences.actions.testSms') : t('notificationPreferences.actions.testSmsDisabled')}
                      </button>
                    </div>
                  )}
                </div>

                {/* Push Notifications */}
                <div className="preference-section">
                  <div className="section-header">
                    <h3>🔔 {t('notificationPreferences.push.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.push.description')}
                      </p>
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.push.critical}
                            onChange={(e) => updatePreference('push.critical', e.target.checked)}
                          />
                          {t('notificationPreferences.push.toggles.critical')}
                        </label>
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.push.warning}
                            onChange={(e) => updatePreference('push.warning', e.target.checked)}
                          />
                          {t('notificationPreferences.push.toggles.warning')}
                        </label>
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.push.info}
                            onChange={(e) => updatePreference('push.info', e.target.checked)}
                          />
                          {t('notificationPreferences.push.toggles.info')}
                        </label>
                      </div>

                      <div className="input-group">
                        <label>{t('notificationPreferences.push.deviceTokenLabel')}</label>
                        <input
                          type="text"
                          value={preferences.push.deviceToken}
                          onChange={(e) => updatePreference('push.deviceToken', e.target.value)}
                          placeholder={t('notificationPreferences.push.placeholders.deviceToken')}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Webhook Notifications */}
                <div className="preference-section">
                  <div className="section-header">
                    <h3>🔗 {t('notificationPreferences.webhook.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.webhook.description')}
                      </p>
                      <div className="input-group">
                        <label>{t('notificationPreferences.webhook.urlLabel')}</label>
                        <input
                          type="url"
                          value={preferences.webhook.url}
                          onChange={(e) => updatePreference('webhook.url', e.target.value)}
                          placeholder={t('notificationPreferences.webhook.placeholders.url')}
                        />
                      </div>
                      
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.webhook.critical}
                            onChange={(e) => updatePreference('webhook.critical', e.target.checked)}
                          />
                          {t('notificationPreferences.webhook.toggles.critical')}
                        </label>
                      </div>
                    </div>
                  )}
                </div>

                {/* Escalation Settings */}
                <div className="preference-section">
                  <div className="section-header">
                    <h3>🚨 {t('notificationPreferences.escalation.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.escalation.description')}
                      </p>
                      <div className="option-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={preferences.escalation.autoEscalate}
                            onChange={(e) => updatePreference('escalation.autoEscalate', e.target.checked)}
                          />
                          {t('notificationPreferences.escalation.autoLabel')}
                        </label>
                      </div>
                      
                      <div className="input-group">
                        <label>{t('notificationPreferences.escalation.delayLabel')}</label>
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
                        <label>{t('notificationPreferences.escalation.maxLabel')}</label>
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
                    <h3>🌙 {t('notificationPreferences.quietHours.title')}</h3>
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
                      <p className="section-description">
                        {t('notificationPreferences.quietHours.description')}
                      </p>
                      <div className="input-group">
                        <label>{t('notificationPreferences.quietHours.startLabel')}</label>
                        <input
                          type="time"
                          value={preferences.quietHours.start}
                          onChange={(e) => updatePreference('quietHours.start', e.target.value)}
                        />
                      </div>
                      
                      <div className="input-group">
                        <label>{t('notificationPreferences.quietHours.endLabel')}</label>
                        <input
                          type="time"
                          value={preferences.quietHours.end}
                          onChange={(e) => updatePreference('quietHours.end', e.target.value)}
                        />
                      </div>
                      
                      <div className="input-group">
                        <label>{t('notificationPreferences.quietHours.timezoneLabel')}</label>
                        <select
                          value={preferences.quietHours.timezone}
                          onChange={(e) => updatePreference('quietHours.timezone', e.target.value)}
                        >
                          {timezoneOptions.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
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
            {t('notificationPreferences.actions.close')}
          </button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? t('notificationPreferences.actions.saving') : t('notificationPreferences.actions.save')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotificationPreferences
