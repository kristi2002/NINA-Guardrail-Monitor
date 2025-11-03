import { useState, useEffect } from 'react'
import axios from 'axios'
import './ConversationEventLog.css'

function ConversationEventLog({ conversationId, isOpen, onClose }) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (conversationId && isOpen) {
      fetchEvents()
    }
  }, [conversationId, isOpen])

  const fetchEvents = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch events from API
      const response = await axios.get(`/api/conversations/${conversationId}/events`)
      
      if (response.data.success) {
        setEvents(response.data.events || [])
      } else {
        setError('Failed to load events')
      }
    } catch (err) {
      console.error('Failed to load events:', err)
      setError('Failed to load events')
      // Fallback to mock data for development
      setEvents(getMockEvents())
    } finally {
      setLoading(false)
    }
  }

  const getMockEvents = () => [
    {
      id: 1,
      conversation_id: conversationId,
      timestamp: '2025-05-10T13:10:00Z',
      type: 'WARNING',
      description: 'Il sistema ha rilevato che ci sono frasi relative alla famiglia con riferimenti a gesti di autolesionismo.',
      details: 'Moderate risk detected',
      severity: 'medium'
    },
    {
      id: 2,
      conversation_id: conversationId,
      timestamp: '2025-05-10T13:05:00Z',
      type: 'INFO',
      description: 'Aree principali analizzate',
      details: 'Analisi completata per: famiglia, autolesionismo, supporto',
      severity: 'low'
    },
    {
      id: 3,
      conversation_id: conversationId,
      timestamp: '2025-05-10T13:00:00Z',
      type: 'INFO',
      description: 'Conversazione Avviata',
      details: 'Sessione terapeutica iniziata con Paziente X',
      severity: 'low'
    },
    {
      id: 4,
      conversation_id: conversationId,
      timestamp: '2025-05-10T12:55:00Z',
      type: 'ALERT',
      description: 'Monitoraggio AI attivato',
      details: 'Sistema di monitoraggio conversazione attivato',
      severity: 'low'
    }
  ]

  const getEventTypeConfig = (type) => {
    const configs = {
      'INFO': { 
        label: 'Info', 
        class: 'event-info', 
        icon: 'ℹ️',
        color: '#1976d2',
        bgColor: '#e3f2fd'
      },
      'WARNING': { 
        label: 'Attenzione', 
        class: 'event-warning', 
        icon: '⚠️',
        color: '#f57c00',
        bgColor: '#fff3e0'
      },
      'ALERT': { 
        label: 'Allarme', 
        class: 'event-alert', 
        icon: '🚨',
        color: '#d32f2f',
        bgColor: '#ffebee'
      }
    }
    return configs[type] || configs['INFO']
  }

  const getSeverityConfig = (severity) => {
    const configs = {
      'low': { label: 'Basso', class: 'severity-low', color: '#4caf50' },
      'medium': { label: 'Medio', class: 'severity-medium', color: '#ffa726' },
      'high': { label: 'Alto', class: 'severity-high', color: '#f44336' }
    }
    return configs[severity] || configs['low']
  }

  const formatDateTime = (dateString) => {
    // Handle null, undefined, or invalid date strings
    if (!dateString) {
      return {
        date: 'N/A',
        time: 'N/A',
        full: 'N/A'
      }
    }

    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return {
        date: 'Data non valida',
        time: 'N/A',
        full: 'Data non valida'
      }
    }

    return {
      date: date.toLocaleDateString('it-IT', { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric' 
      }),
      time: date.toLocaleTimeString('it-IT', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      full: date.toLocaleString('it-IT')
    }
  }

  const getRelativeTime = (dateString) => {
    const now = new Date()
    const eventTime = new Date(dateString)
    const diffMs = now - eventTime
    const diffMinutes = Math.floor(diffMs / 60000)
    
    if (diffMinutes < 1) return 'Ora'
    if (diffMinutes < 60) return `${diffMinutes}m fa`
    
    const diffHours = Math.floor(diffMinutes / 60)
    if (diffHours < 24) return `${diffHours}h fa`
    
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}g fa`
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="conversation-event-log-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <h2>Log Eventi Conversazione</h2>
          <div className="header-actions">
            <button 
              className="btn-refresh"
              onClick={fetchEvents}
              disabled={loading}
            >
              {loading ? '⏳' : '🔄'} Aggiorna
            </button>
            <button className="modal-close" onClick={onClose}>
              ✕
            </button>
          </div>
        </div>

        {/* Event Statistics */}
        <div className="event-stats">
          <div className="stat-item">
            <span className="stat-number">{events.length}</span>
            <span className="stat-label">Eventi Totali</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">
              {events.filter(e => e.type === 'WARNING' || e.type === 'ALERT').length}
            </span>
            <span className="stat-label">Allarmi</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">
              {events.filter(e => e.severity === 'high').length}
            </span>
            <span className="stat-label">Alta Priorità</span>
          </div>
        </div>

        {/* Event List */}
        <div className="event-log-container">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Caricamento eventi...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <div className="error-icon">⚠️</div>
              <p>{error}</p>
              <button className="btn-retry" onClick={fetchEvents}>
                Riprova
              </button>
            </div>
          ) : events.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📝</div>
              <p>Nessun evento registrato</p>
              <p className="empty-subtitle">Gli eventi della conversazione appariranno qui</p>
            </div>
          ) : (
            <div className="event-timeline">
              {events.map((event, index) => {
                const eventConfig = getEventTypeConfig(event.type)
                const severityConfig = getSeverityConfig(event.severity)
                const eventDate = formatDateTime(event.timestamp)
                const relativeTime = getRelativeTime(event.timestamp)
                
                return (
                  <div 
                    key={event.id} 
                    className={`event-item ${eventConfig.class} ${index === 0 ? 'latest' : ''}`}
                  >
                    <div className="event-timeline-marker">
                      <div className="event-icon">{eventConfig.icon}</div>
                      {index < events.length - 1 && <div className="timeline-line"></div>}
                    </div>
                    
                    <div className="event-content">
                      <div className="event-header">
                        <div className="event-type">
                          <span className={`type-badge ${eventConfig.class}`}>
                            {eventConfig.icon} {eventConfig.label}
                          </span>
                          <span className={`severity-badge ${severityConfig.class}`}>
                            {severityConfig.label}
                          </span>
                        </div>
                        <div className="event-time">
                          <span className="relative-time">{relativeTime}</span>
                          <span className="absolute-time">{eventDate.full}</span>
                        </div>
                      </div>
                      
                      <div className="event-description">
                        {event.description}
                      </div>
                      
                      {event.details && (
                        <div className="event-details">
                          <strong>Dettagli:</strong> {event.details}
                        </div>
                      )}
                      
                      <div className="event-metadata">
                        <span className="event-id">ID: {event.id}</span>
                        <span className="event-severity">
                          Severità: <span style={{ color: severityConfig.color }}>
                            {severityConfig.label}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="modal-footer">
          <button className="btn-export">
            📄 Esporta Log
          </button>
          <button className="btn-close" onClick={onClose}>
            Chiudi
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConversationEventLog
