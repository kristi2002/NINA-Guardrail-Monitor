import { useState, useEffect } from 'react'
import axios from 'axios'
import { mapEventTypeToDisplay, getEventTypeLabel, getEventTypeIcon } from '../utils/eventTypeMapper'
import ConversationReportModal from './ConversationReportModal'
import './ConversationDetailModal.css'

function ConversationDetailModal({ conversation, isOpen, onClose, onConversationUpdated }) {
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState([])
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [fullConversation, setFullConversation] = useState(null)

  useEffect(() => {
    const fetchConversationDetails = async () => {
      if (!conversation || !isOpen) return
      
      try {
        setLoading(true)
        const response = await axios.get(`/api/conversations/${conversation.id}`)
        
        if (response.data.success) {
          const detailedConversation = response.data.conversation
          setFullConversation(detailedConversation)
          // Get events from the detailed conversation
          setEvents(detailedConversation.events || detailedConversation.recent_events || [])
        } else {
          // Fallback to conversation from props
          setEvents(conversation.events || [])
          setFullConversation(conversation)
        }
      } catch (err) {
        console.error('Failed to load conversation details:', err)
        // Fallback to conversation from props
        setEvents(conversation.events || [])
        setFullConversation(conversation)
      } finally {
        setLoading(false)
      }
    }
    
    if (conversation && isOpen) {
      // Fetch full conversation details including events
      fetchConversationDetails()
    }
  }, [conversation?.id, isOpen])

  if (!isOpen || !conversation) {
    return null
  }

  // Use fullConversation if available, fallback to conversation from props
  const displayConversation = fullConversation || conversation

  const formatDateTime = (dateString) => {
    // Handle null, undefined, or invalid date strings
    if (!dateString) {
      return {
        date: 'N/A',
        time: 'N/A'
      }
    }

    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return {
        date: 'Data non valida',
        time: 'N/A'
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
      })
    }
  }

  const getSituationConfig = (situation, level) => {
    const configs = {
      'Regolare': { 
        label: 'Tutto regolare', 
        class: 'situation-regular', 
        icon: '👍',
        description: 'Niente da segnalare',
        color: '#51cf66'
      },
      'Segni di autolesionismo': { 
        label: 'Attenzione', 
        class: 'situation-warning', 
        icon: '⚠️',
        description: 'Durante la conversazione sono stati utilizzati termini che possono far credere a dei possibili gesti di autolesionismo con rischio moderato.',
        color: '#ffa726'
      },
      'Gesti pericolosi': { 
        label: 'Allarme', 
        class: 'situation-danger', 
        icon: '🚨',
        description: 'Livello massimo di pericolosità rilevato. Sono stati utilizzati termini di lesioni gravi autoinflitte',
        color: '#f44336'
      }
    }
    return configs[situation] || configs['Regolare']
  }

  const getEventTypeConfig = (eventType, severity) => {
    // Map backend event_type to display type
    const displayType = mapEventTypeToDisplay(eventType, severity)
    
    const configs = {
      'INFO': { label: 'Info', class: 'event-info', icon: 'ℹ️' },
      'WARNING': { label: 'Attenzione', class: 'event-warning', icon: '⚠️' },
      'ALERT': { label: 'Allarme', class: 'event-alert', icon: '🚨' }
    }
    
    const config = configs[displayType] || configs['INFO']
    
    // Enhance with backend-specific info if available
    if (eventType) {
      const backendIcon = getEventTypeIcon(eventType)
      const backendLabel = getEventTypeLabel(eventType)
      return {
        ...config,
        icon: backendIcon,
        label: backendLabel
      }
    }
    
    return config
  }

  const handleStopAndReport = async () => {
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/stop`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Conversazione fermata e segnalata con successo')
        
        // Update conversation status
        const updatedConversation = {
          ...conversation,
          status: 'STOPPED'
        }
        
        if (onConversationUpdated) {
          onConversationUpdated(updatedConversation)
        }
        
        onClose()
      } else {
        alert('Errore nel fermare la conversazione')
      }
    } catch (error) {
      console.error('Failed to stop conversation:', error)
      alert('Errore nel fermare la conversazione')
    } finally {
      setLoading(false)
    }
  }

  const handleUnreliableAlarm = async () => {
    try {
      setLoading(true)
      const response = await axios.put(`/api/conversations/${conversation.id}/situation`, {
        situation: 'Regolare',
        level: 'low'
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Allarme marcato come non attendibile')
        
        // Update conversation situation
        const updatedConversation = {
          ...conversation,
          situation: 'Regolare',
          situationLevel: 'low'
        }
        
        if (onConversationUpdated) {
          onConversationUpdated(updatedConversation)
        }
        
        onClose()
      } else {
        alert('Errore nel marcare l\'allarme come non attendibile')
      }
    } catch (error) {
      console.error('Failed to mark alarm as unreliable:', error)
      alert('Errore nel marcare l\'allarme come non attendibile')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true)
      const response = await axios.get(`/api/conversations/${conversation.id}/report`)
      
      if (response.data.success) {
        console.log('API report data:', response.data.report)
        console.log('API patientInfo:', response.data.report.patientInfo)
        setReportData(response.data.report)
        setShowReportModal(true)
      } else {
        alert('Errore nella generazione del report')
      }
    } catch (error) {
      console.error('Failed to generate report:', error)
      // Fallback to mock data for development
      setReportData(generateMockReport())
      setShowReportModal(true)
    } finally {
      setGeneratingReport(false)
    }
  }

  const generateMockReport = () => {
    const displayConv = displayConversation
    const createdDate = formatDateTime(
      displayConv.created_at || 
      displayConv.createdAt || 
      displayConv.session_start
    )
    console.log('Mock report - conversation data:', displayConv)
    console.log('Mock report - patientInfo:', displayConv.patientInfo)
    return {
      id: displayConv.id,
      patientId: displayConv.patientId || displayConv.patient_id,
      patientInfo: displayConv.patientInfo || { 
        name: `Paziente ${displayConv.patientId || displayConv.patient_id || displayConv.id}`,
        age: 45, 
        gender: 'M',
        pathology: 'Non specificata'
      },
      conversationDate: createdDate.date,
      conversationTime: createdDate.time,
      duration: displayConv.duration || displayConv.session_duration_minutes || 0,
      status: displayConv.status,
      situation: displayConv.situation || 'Normale',
      situationLevel: displayConv.situationLevel || 'low',
      events: events,
      summary: {
        totalEvents: events.length,
        warningEvents: events.filter(e => {
          const eventType = e.event_type || e.type
          const severity = e.severity
          return mapEventTypeToDisplay(eventType, severity) === 'WARNING'
        }).length,
        alertEvents: events.filter(e => {
          const eventType = e.event_type || e.type
          const severity = e.severity
          return mapEventTypeToDisplay(eventType, severity) === 'ALERT'
        }).length,
        riskLevel: displayConv.situationLevel || 'low',
        recommendations: getRecommendations(displayConv.situationLevel || 'low')
      },
      analysis: {
        keyTopics: ['famiglia', 'autolesionismo', 'supporto emotivo'],
        emotionalTone: 'preoccupato',
        riskFactors: displayConv.situationLevel === 'high' ? ['gesti pericolosi', 'termini auto-lesivi'] : [],
        positiveAspects: ['apertura al dialogo', 'ricerca di aiuto']
      },
      generatedAt: new Date().toISOString()
    }
  }

  const getRecommendations = (riskLevel) => {
    switch (riskLevel) {
      case 'high':
        return [
          'Intervento immediato richiesto',
          'Contatto con servizi di emergenza',
          'Valutazione psichiatrica urgente',
          'Supporto familiare attivato'
        ]
      case 'medium':
        return [
          'Monitoraggio intensificato',
          'Sessione di follow-up programmata',
          'Valutazione psicologica',
          'Supporto terapeutico continuato'
        ]
      default:
        return [
          'Continuare il monitoraggio',
          'Sessione di follow-up standard',
          'Supporto preventivo'
        ]
    }
  }

  const createdDate = formatDateTime(
    displayConversation.created_at || 
    displayConversation.createdAt || 
    displayConversation.session_start
  )
  const situationConfig = getSituationConfig(displayConversation.situation, displayConversation.situationLevel)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="conversation-detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <h2>Dettaglio conversazione</h2>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Patient Information */}
        <div className="patient-info-card">
          <div className="patient-header">
            <div className="patient-avatar-large">
              <span className="patient-icon">👤</span>
              <span className="patient-badge">1</span>
            </div>
            <div className="patient-details">
              <h3>{displayConversation.patientInfo?.name || `Paziente ${displayConversation.patientId || displayConversation.patient_id}`}</h3>
              <div className="patient-meta">
                <span>Età: {displayConversation.patientInfo?.age || 'N/A'} anni</span>
                <span>Sesso: {displayConversation.patientInfo?.gender || 'N/A'}</span>
                <span>Patologia: {displayConversation.patientInfo?.pathology || 'N/A'}</span>
              </div>
            </div>
          </div>
          
          <div className="conversation-info">
            <h4>Conversazione del {createdDate.date}</h4>
            <p>Inizio ore {createdDate.time} - Stato: <span className="status-text">{displayConversation.status}</span> (Durata {displayConversation.duration || displayConversation.session_duration_minutes || 0} min)</p>
          </div>
        </div>

        {/* Alert Box */}
        {displayConversation.situation !== 'Regolare' && (
          <div className={`alert-box ${situationConfig.class}`}>
            <div className="alert-icon">{situationConfig.icon}</div>
            <div className="alert-content">
              <h4>{situationConfig.label}</h4>
              <p>{situationConfig.description}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="action-buttons">
          <button 
            className="btn-stop-report"
            onClick={handleStopAndReport}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Elaborazione...
              </>
            ) : (
              'Ferma e segnala'
            )}
          </button>
          
          <button 
            className="btn-unreliable-alarm"
            onClick={handleUnreliableAlarm}
            disabled={loading}
          >
            <span className="btn-icon">👤</span>
            Allarme non attendibile
          </button>
        </div>

        {/* Conversation Report */}
        <div className="conversation-report">
          <h4>Visualizzazione report conversazione</h4>
          <div className="report-icons">
            <div className="report-icon">
              <span className="icon">👤</span>
              <span className="icon-badge">1</span>
            </div>
            <div 
              className={`report-pdf ${generatingReport ? 'generating' : ''}`}
              onClick={handleGenerateReport}
              style={{ cursor: 'pointer' }}
            >
              <span className="pdf-icon">
                {generatingReport ? '⏳' : '📄'}
              </span>
              <span className="pdf-text">
                {generatingReport ? 'Generazione...' : 'PDF'}
              </span>
            </div>
          </div>
        </div>

        {/* Event Log */}
        <div className="event-log">
          <h4>Eventi conversazione</h4>
          <div className="event-table-container">
            <table className="event-table">
              <thead>
                <tr>
                  <th>Evento</th>
                  <th>Descrizione</th>
                  <th>Dettagli</th>
                </tr>
              </thead>
              <tbody>
                {events.length > 0 ? (
                  events.map((event, index) => {
                    const eventDate = formatDateTime(event.timestamp)
                    // Support both old 'type' and new 'event_type' fields
                    const eventType = event.event_type || event.type
                    const eventConfig = getEventTypeConfig(eventType, event.severity)
                    
                    return (
                      <tr key={index} className={`event-row ${eventConfig.class}`}>
                        <td className="event-time">
                          <div className="event-timestamp">
                            {eventDate.date}, {eventDate.time}
                          </div>
                          <div className={`event-type ${eventConfig.class}`}>
                            {eventConfig.icon} {eventConfig.label}
                          </div>
                        </td>
                        <td className="event-description">
                          {event.description || event.message_content || event.message || 'No description available'}
                        </td>
                        <td className="event-details">
                          {event.details || event.context || '-'}
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan="3" className="no-events">
                      Nessun evento registrato
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="status-indicators">
          <div className="status-alternative">
            <span className="alternative-label">Alternative</span>
          </div>
          
          <div className={`status-box ${situationConfig.class}`}>
            <div className="status-icon">
              {situationConfig.icon}
            </div>
            <div className="status-content">
              <h4>{situationConfig.label}</h4>
              <p>{situationConfig.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Conversation Report Modal */}
      {showReportModal && reportData && (
        <ConversationReportModal
          reportData={reportData}
          isOpen={showReportModal}
          onClose={() => {
            setShowReportModal(false)
            setReportData(null)
          }}
        />
      )}
    </div>
  )
}

export default ConversationDetailModal
