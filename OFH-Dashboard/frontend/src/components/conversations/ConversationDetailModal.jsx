import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { mapEventTypeToDisplay, getEventTypeLabel, getEventTypeIcon } from '../../utils/eventTypeMapper'
import ConversationReportModal from './ConversationReportModal'
import './ConversationDetailModal.css'

// Action templates for common scenarios
const ACTION_TEMPLATES = {
  escalate: [
    'Richiede intervento supervisore',
    'Situazione complessa che richiede escalation',
    'Decisione che richiede approvazione superiore',
    'Caso che necessita di revisione manageriale'
  ],
  manual_intervention: [
    'Richiede valutazione umana immediata',
    'Situazione ambigua che necessita di intervento',
    'Caso che richiede expertise specializzata',
    'Decisione che richiede giudizio umano'
  ],
  override_guardrail: [
    'Falso positivo del guardrail',
    'Guardrail troppo restrittivo per questo caso',
    'Decisione del guardrail non appropriata',
    'Override necessario per procedere'
  ],
  system_override: [
    'Bypass necessario per caso speciale',
    'Sistema troppo conservativo per questa situazione',
    'Override richiesto per continuare operazione',
    'Bypass autorizzato per caso eccezionale'
  ],
  emergency_stop: [
    'Minaccia di sicurezza rilevata',
    'Violazione critica del protocollo',
    'Situazione di emergenza immediata',
    'Stop richiesto per sicurezza'
  ],
  resolve: [
    'Problema risolto con successo',
    'Situazione normalizzata',
    'Issue chiusa dopo intervento',
    'Risoluzione completata'
  ]
}

// Action severity levels for confirmation requirements
const ACTION_SEVERITY = {
  low: ['acknowledge', 'resolve'],
  medium: ['escalate', 'manual_intervention', 'override_guardrail', 'stop_conversation', 'complete_conversation', 'cancel_conversation', 'resume_conversation'],
  high: ['system_override'],
  critical: ['emergency_stop']
}

function ConversationDetailModal({ conversation, isOpen, onClose, onConversationUpdated }) {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [fetchingDetails, setFetchingDetails] = useState(false)
  const [events, setEvents] = useState([])
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [fullConversation, setFullConversation] = useState(null)
  const [recentActions, setRecentActions] = useState([])
  const [showActionHistory, setShowActionHistory] = useState(false)

  useEffect(() => {
    const fetchConversationDetails = async () => {
      if (!conversation || !isOpen) return
      
      // Reset loading state when modal opens
      setLoading(false)
      
      try {
        setFetchingDetails(true)
        const response = await axios.get(`/api/conversations/${conversation.id}`)
        
        if (response.data.success) {
          const detailedConversation = response.data.conversation
          console.log('Fetched conversation details:', detailedConversation)
          console.log('Patient info:', detailedConversation.patientInfo)
          setFullConversation(detailedConversation)
          // Get events from the detailed conversation
          setEvents(detailedConversation.events || detailedConversation.recent_events || [])
          // Get recent actions for action history
          setRecentActions(detailedConversation.recent_actions || [])
        } else {
          // Fallback to conversation from props
          setEvents(conversation.events || [])
          setFullConversation(conversation)
          setRecentActions([])
        }
      } catch (err) {
        console.error('Failed to load conversation details:', err)
        // Fallback to conversation from props
        setEvents(conversation.events || [])
        setFullConversation(conversation)
        setRecentActions([])
      } finally {
        setFetchingDetails(false)
      }
    }
    
    if (conversation && isOpen) {
      // Fetch full conversation details including events
      fetchConversationDetails()
    }
  }, [conversation?.id, isOpen])

  // Helper function to check if action is available based on conversation state
  const isActionAvailable = (actionType) => {
    switch (actionType) {
      case 'resume':
        return ['STOPPED', 'PAUSED'].includes(currentStatus)
      case 'stop':
      case 'emergency_stop':
        return ['ACTIVE', 'PAUSED'].includes(currentStatus)
      case 'complete':
        return ['ACTIVE'].includes(currentStatus)
      case 'cancel':
        return ['ACTIVE', 'PAUSED'].includes(currentStatus)
      case 'escalate':
      case 'manual_intervention':
        return !['COMPLETED', 'CANCELLED'].includes(currentStatus)
      default:
        return true
    }
  }

  // Helper function to get action severity
  const getActionSeverity = (actionType) => {
    for (const [severity, actions] of Object.entries(ACTION_SEVERITY)) {
      if (actions.includes(actionType)) {
        return severity
      }
    }
    return 'medium'
  }

  // Helper function to show prompt with templates
  const promptWithTemplates = (actionType, defaultMessage) => {
    const templates = ACTION_TEMPLATES[actionType] || []
    if (templates.length === 0) {
      return window.prompt(defaultMessage, '')
    }

    // Create a custom prompt with template selection
    const templateChoice = window.prompt(
      `${defaultMessage}\n\nTemplate disponibili:\n${templates.map((t, i) => `${i + 1}. ${t}`).join('\n')}\n\nInserisci il numero del template (1-${templates.length}) o scrivi un motivo personalizzato:`,
      ''
    )

    if (templateChoice === null) return null

    // Check if user selected a template number
    const templateNum = parseInt(templateChoice)
    if (!isNaN(templateNum) && templateNum >= 1 && templateNum <= templates.length) {
      return templates[templateNum - 1]
    }

    // Otherwise return the custom text
    return templateChoice
  }

  // Helper function for severity-based confirmation
  const confirmWithSeverity = (actionType, message, additionalInfo = '') => {
    const severity = getActionSeverity(actionType)
    
    if (severity === 'low') {
      // Low severity: simple confirmation
      return window.confirm(message + (additionalInfo ? `\n\n${additionalInfo}` : ''))
    } else if (severity === 'medium') {
      // Medium severity: standard confirmation
      return window.confirm(`⚠️ ${message}${additionalInfo ? `\n\n${additionalInfo}` : ''}\n\nProcedere?`)
    } else if (severity === 'high') {
      // High severity: strong warning
      return window.confirm(`⚠️ ATTENZIONE: ${message}${additionalInfo ? `\n\n${additionalInfo}` : ''}\n\nQuesta è un'azione importante. Sei sicuro di voler procedere?`)
    } else if (severity === 'critical') {
      // Critical severity: double confirmation
      const firstConfirm = window.confirm(`🚨 AZIONE CRITICA: ${message}${additionalInfo ? `\n\n${additionalInfo}` : ''}\n\nQuesta è un'azione critica che richiede conferma.`)
      if (!firstConfirm) return false
      return window.confirm(`🚨 CONFERMA FINALE\n\nSei assolutamente sicuro di voler procedere con questa azione critica?`)
    }
    
    return window.confirm(message)
  }

  const formatDateTime = (dateString) => {
    const locale = i18n.language?.startsWith('it') ? 'it-IT' : 'en-US'
    // Handle null, undefined, or invalid date strings
    if (!dateString) {
      return {
        date: notAvailableText,
        time: notAvailableText
      }
    }

    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return {
        date: invalidDateText,
        time: notAvailableText
      }
    }

    return {
      date: date.toLocaleDateString(locale, { 
        day: 'numeric', 
        month: 'long', 
        year: 'numeric' 
      }),
      time: date.toLocaleTimeString(locale, { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
  }

  const formatEventDetails = (details) => {
    if (!details) {
      return noEventDetailsText
    }

    // If it's a string, try to parse it as JSON
    let detailsObj = details
    if (typeof details === 'string') {
      try {
        detailsObj = JSON.parse(details)
      } catch (e) {
        // If it's not JSON, return the string as-is
        return details
      }
    }

    // If it's an object, filter out null/undefined values and format nicely
    if (typeof detailsObj === 'object' && detailsObj !== null && !Array.isArray(detailsObj)) {
      const filtered = Object.fromEntries(
        Object.entries(detailsObj).filter(([_, value]) => value !== null && value !== undefined && value !== '')
      )

      if (Object.keys(filtered).length === 0) {
        return noEventDetailsText
      }

      // Format as a user-friendly list instead of raw JSON
      return (
        <div className="event-details-list">
          {Object.entries(filtered).map(([key, value]) => {
            // Format key labels
            const label = key
              .replace(/_/g, ' ')
              .replace(/\b\w/g, l => l.toUpperCase())
            
            // Format values nicely
            let displayValue = value
            if (typeof value === 'object' && value !== null) {
              displayValue = JSON.stringify(value, null, 2)
            } else if (typeof value === 'number') {
              if (key.includes('score') || key.includes('confidence')) {
                displayValue = `${(value * 100).toFixed(1)}%`
              } else if (key.includes('time') || key.includes('duration')) {
                displayValue = `${value}ms`
              } else {
                displayValue = value.toString()
              }
            } else {
              displayValue = String(value)
            }

            return (
              <div key={key} className="event-detail-item">
                <span className="detail-label">{label}:</span>
                <span className="detail-value">{displayValue}</span>
              </div>
            )
          })}
        </div>
      )
    }

    // Fallback for arrays or other types
    return JSON.stringify(detailsObj, null, 2)
  }

  const situationConfigs = useMemo(
    () => ({
      regular: {
        label: t('conversationDetail.situation.regular.title'),
        class: 'situation-regular',
        icon: '👍',
        description: t('conversationDetail.situation.regular.description'),
        color: '#51cf66'
      },
      warning: {
        label: t('conversationDetail.situation.warning.title'),
        class: 'situation-warning',
        icon: '⚠️',
        description: t('conversationDetail.situation.warning.description'),
        color: '#ffa726'
      },
      danger: {
        label: t('conversationDetail.situation.danger.title'),
        class: 'situation-danger',
        icon: '🚨',
        description: t('conversationDetail.situation.danger.description'),
        color: '#f44336'
      }
    }),
    [t]
  )

  if (!isOpen || !conversation) {
    return null
  }

  // Use fullConversation if available, fallback to conversation from props
  const displayConversation = fullConversation || conversation
  const currentStatus = displayConversation?.status?.toUpperCase() || 'UNKNOWN'

  const getSituationConfig = (situation, level) => {
    // First check risk_level (most authoritative) - it takes priority over situation text
    const normalizedLevel = (level || 'low').toLowerCase()
    let key = 'regular'
    
    if (normalizedLevel === 'high' || normalizedLevel === 'critical') {
      key = 'danger'
    } else if (normalizedLevel === 'medium') {
      key = 'warning'
    } else {
      // Only check situation text if level is not HIGH/CRITICAL/MEDIUM
      const normalizedSituation = (situation || '').toLowerCase()

      if (
        normalizedSituation.includes('gesti') ||
        normalizedSituation.includes('danger') ||
        normalizedSituation.includes('severe')
      ) {
        key = 'danger'
      } else if (
        normalizedSituation.includes('autoles') ||
        normalizedSituation.includes('self') ||
        normalizedSituation.includes('warning') ||
        normalizedSituation.includes('moderate')
      ) {
        key = 'warning'
      } else if (
        normalizedSituation.includes('regolar') ||
        normalizedSituation.includes('regular') ||
        normalizedSituation.includes('low')
      ) {
        key = 'regular'
      }
    }

    return situationConfigs[key] || situationConfigs.regular
  }

  const getEventTypeConfig = (eventType, severity) => {
    // Map backend event_type to display type
    const displayType = mapEventTypeToDisplay(eventType, severity)
    
    const configs = {
      INFO: { label: t('conversationDetail.events.info'), class: 'event-info', icon: 'ℹ️' },
      WARNING: { label: t('conversationDetail.events.warning'), class: 'event-warning', icon: '⚠️' },
      ALERT: { label: t('conversationDetail.events.alert'), class: 'event-alert', icon: '🚨' }
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

  const processingText = t('conversationDetail.common.processing')
  const sectionTitles = {
    lifecycle: t('conversationDetail.sections.lifecycle'),
    escalation: t('conversationDetail.sections.escalation'),
    system: t('conversationDetail.sections.systemControl'),
    report: t('conversationDetail.sections.report'),
    events: t('conversationDetail.sections.events'),
    alternative: t('conversationDetail.sections.alternative')
  }
  const actionLabels = {
    stopReport: t('conversationDetail.actions.stopReport.label'),
    complete: t('conversationDetail.actions.complete.label'),
    cancel: t('conversationDetail.actions.cancel.label'),
    resume: t('conversationDetail.actions.resume.label'),
    emergencyStop: t('conversationDetail.actions.emergencyStop.label'),
    escalate: t('conversationDetail.actions.escalate.label'),
    manualIntervention: t('conversationDetail.actions.manualIntervention.label'),
    acknowledge: t('conversationDetail.actions.acknowledge.label'),
    resolve: t('conversationDetail.actions.resolve.label'),
    overrideGuardrail: t('conversationDetail.actions.overrideGuardrail.label'),
    systemOverride: t('conversationDetail.actions.systemOverride.label'),
    unreliableAlarm: t('conversationDetail.actions.unreliableAlarm.label')
  }
  const actionTooltips = {
    stopReport: t('conversationDetail.actions.stopReport.tooltip'),
    resume: t('conversationDetail.actions.resume.tooltip'),
    emergencyStop: t('conversationDetail.actions.emergencyStop.tooltip'),
    escalate: t('conversationDetail.actions.escalate.tooltip'),
    manualIntervention: t('conversationDetail.actions.manualIntervention.tooltip'),
    overrideGuardrail: t('conversationDetail.actions.overrideGuardrail.tooltip'),
    systemOverride: t('conversationDetail.actions.systemOverride.tooltip')
  }
  const reportGenerating = t('conversationDetail.report.generating')
  const reportPdf = t('conversationDetail.report.pdf')
  const eventTableHeaders = {
    event: t('conversationDetail.events.table.event'),
    description: t('conversationDetail.events.table.description'),
    details: t('conversationDetail.events.table.details'),
    none: t('conversationDetail.events.table.empty'),
    noDescription: t('conversationDetail.events.noDescription')
  }
  const noEventDetailsText = t('conversationDetail.events.noDetails')
  const notAvailableText = t('conversationDetail.common.notAvailable')
  const invalidDateText = t('conversationDetail.common.invalidDate')

  const handleStopAndReport = async () => {
    if (!isActionAvailable('stop')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const confirmed = confirmWithSeverity(
      'stop_conversation',
      'Ferma e Segnala',
      'Questa azione fermerà la conversazione normalmente.\nLa conversazione verrà segnalata come interrotta dall\'amministratore.\n\nPer situazioni di emergenza critica, usa invece "Fermata Emergenza".'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/stop`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        let message = 'Conversazione fermata e segnalata con successo'
        
        // Show warning if Kafka failed but operation succeeded
        if (response.data.warning) {
          message += `\n\n⚠️ Avviso: ${response.data.warning}`
        }
        
        alert(message)
        
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
        // Show specific error message from backend
        const errorMessage = response.data.message || response.data.error || 'Errore nel fermare la conversazione'
        alert(`Errore nel fermare la conversazione:\n${errorMessage}`)
      }
    } catch (error) {
      console.error('Failed to stop conversation:', error)
      
      // Show detailed error message
      let errorMessage = 'Errore nel fermare la conversazione'
      if (error.response?.data?.message) {
        errorMessage += `\n${error.response.data.message}`
      } else if (error.response?.data?.error) {
        errorMessage += `\n${error.response.data.error}`
      } else if (error.message) {
        errorMessage += `\n${error.message}`
      }
      
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleCompleteConversation = async () => {
    if (!isActionAvailable('complete')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const confirmed = confirmWithSeverity(
      'complete_conversation',
      'Completa conversazione',
      'Questa azione segnerà la conversazione come completata.'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/complete`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Conversazione completata con successo')
        
        // Update conversation status
        const updatedConversation = {
          ...conversation,
          status: 'COMPLETED'
        }
        
        if (onConversationUpdated) {
          onConversationUpdated(updatedConversation)
        }
        
        onClose()
      } else {
        const errorMessage = response.data.message || response.data.error || 'Errore nel completare la conversazione'
        alert(`Errore nel completare la conversazione:\n${errorMessage}`)
      }
    } catch (error) {
      console.error('Failed to complete conversation:', error)
      let errorMessage = 'Errore nel completare la conversazione'
      if (error.response?.data?.message) {
        errorMessage += `\n${error.response.data.message}`
      } else if (error.response?.data?.error) {
        errorMessage += `\n${error.response.data.error}`
      } else if (error.message) {
        errorMessage += `\n${error.message}`
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelConversation = async () => {
    if (!isActionAvailable('cancel')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const confirmed = confirmWithSeverity(
      'cancel_conversation',
      'Annulla conversazione',
      'Questa azione segnerà la conversazione come annullata.\nQuesta azione è diversa da "Ferma e segnala" che indica un intervento durante la sessione.'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/cancel`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Conversazione annullata con successo')
        
        // Update conversation status
        const updatedConversation = {
          ...conversation,
          status: 'CANCELLED'
        }
        
        if (onConversationUpdated) {
          onConversationUpdated(updatedConversation)
        }
        
        onClose()
      } else {
        const errorMessage = response.data.message || response.data.error || 'Errore nell\'annullare la conversazione'
        alert(`Errore nell'annullare la conversazione:\n${errorMessage}`)
      }
    } catch (error) {
      console.error('Failed to cancel conversation:', error)
      let errorMessage = 'Errore nell\'annullare la conversazione'
      if (error.response?.data?.message) {
        errorMessage += `\n${error.response.data.message}`
      } else if (error.response?.data?.error) {
        errorMessage += `\n${error.response.data.error}`
      } else if (error.message) {
        errorMessage += `\n${error.message}`
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleEscalate = async () => {
    if (!isActionAvailable('escalate')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const reason = promptWithTemplates('escalate', 'Inserisci il motivo dell\'escalation al supervisore:')
    if (reason === null || reason === '') return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/escalate`, {
        reason: reason || 'Escalated by operator',
        message: `Conversation escalated: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Conversazione escalata con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation, status: 'ESCALATED' })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nell\'escalation'}`)
      }
    } catch (error) {
      console.error('Failed to escalate conversation:', error)
      alert(`Errore nell'escalation: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async () => {
    const reason = window.prompt('Inserisci il motivo del riconoscimento (opzionale):', '')
    if (reason === null) return // User cancelled (but allow empty string)
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/acknowledge`, {
        reason: reason || 'Acknowledged by operator',
        message: `Conversation acknowledged${reason ? `: ${reason}` : ''}`
      })
      
      if (response.data.success) {
        alert('Conversazione riconosciuta con successo')
        if (onConversationUpdated) {
          onConversationUpdated(conversation)
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nel riconoscimento'}`)
      }
    } catch (error) {
      console.error('Failed to acknowledge conversation:', error)
      alert(`Errore nel riconoscimento: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async () => {
    const reason = promptWithTemplates('resolve', 'Inserisci le note di risoluzione:')
    if (reason === null || reason === '') return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/resolve`, {
        reason: reason || 'Resolved by operator',
        message: `Conversation resolved: ${reason || 'No notes provided'}`,
        resolution_notes: reason || 'Resolved by operator'
      })
      
      if (response.data.success) {
        alert('Conversazione risolta con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation, requires_attention: false })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nella risoluzione'}`)
      }
    } catch (error) {
      console.error('Failed to resolve conversation:', error)
      alert(`Errore nella risoluzione: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleOverrideGuardrail = async () => {
    const reason = promptWithTemplates('override_guardrail', 'Inserisci il motivo per sovrascrivere la decisione del guardrail:')
    if (reason === null || reason === '') return
    
    const confirmed = confirmWithSeverity(
      'override_guardrail',
      'Sovrascrivi Guardrail',
      'Questa azione sovrascriverà una decisione specifica del guardrail.\nUtile quando un guardrail ha generato un falso positivo.\n\nDifferenza da "Override Sistema":\n• Sovrascrivi Guardrail: Per decisioni specifiche del guardrail\n• Override Sistema: Per bypass a livello di sistema completo'
    )
    
    if (!confirmed) return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/override-guardrail`, {
        reason: reason || 'Guardrail override by operator',
        message: `Guardrail decision overridden: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Guardrail sovrascritto con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nella sovrascrittura del guardrail'}`)
      }
    } catch (error) {
      console.error('Failed to override guardrail:', error)
      alert(`Errore nella sovrascrittura: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleManualIntervention = async () => {
    if (!isActionAvailable('manual_intervention')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const reason = promptWithTemplates('manual_intervention', 'Inserisci il motivo per richiedere l\'intervento manuale urgente:')
    if (reason === null || reason === '') return
    
    const confirmed = confirmWithSeverity(
      'manual_intervention',
      'Richiesta Intervento Manuale',
      'Questa azione richiede un intervento manuale urgente.\nAumenterà il livello di rischio e imposterà "richiede attenzione".\n\nDifferenza da "Escala":\n• Intervento Manuale: Richiesta urgente per revisione umana (priorità URGENT)\n• Escala: Escalation formale al supervisore (cambia status a ESCALATED)'
    )
    
    if (!confirmed) return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/manual-intervention`, {
        reason: reason || 'Manual intervention required',
        message: `Manual intervention requested: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Intervento manuale richiesto con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation, requires_attention: true })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nella richiesta di intervento manuale'}`)
      }
    } catch (error) {
      console.error('Failed to request manual intervention:', error)
      alert(`Errore nella richiesta: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSystemOverride = async () => {
    const reason = promptWithTemplates('system_override', 'Inserisci il motivo per l\'override di sistema:')
    if (reason === null || reason === '') return
    
    const confirmed = confirmWithSeverity(
      'system_override',
      'Override di Sistema',
      'Questa azione attiverà un override a livello di sistema completo.\nRidurrà il livello di rischio a LOW e bypasserà i controlli del sistema.\n\nDifferenza da "Sovrascrivi Guardrail":\n• Override Sistema: Bypass completo del sistema (riduce rischio a LOW)\n• Sovrascrivi Guardrail: Solo per decisioni specifiche del guardrail'
    )
    
    if (!confirmed) return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/system-override`, {
        reason: reason || 'System-level override',
        message: `System override activated: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Override di sistema attivato con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nell\'attivazione dell\'override di sistema'}`)
      }
    } catch (error) {
      console.error('Failed to activate system override:', error)
      alert(`Errore nell'attivazione: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleEmergencyStop = async () => {
    if (!isActionAvailable('emergency_stop')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const reason = promptWithTemplates('emergency_stop', 'Inserisci il motivo per la fermata di emergenza:')
    if (reason === null || reason === '') return
    
    const confirmed = confirmWithSeverity(
      'emergency_stop',
      'FERMATA DI EMERGENZA',
      'Questa azione fermerà immediatamente la conversazione e imposterà il livello di rischio come CRITICO.\n\nDifferenza da "Ferma e segnala":\n• Fermata Emergenza: Situazioni critiche urgenti (rischio CRITICO)\n• Ferma e segnala: Interruzione normale (rischio invariato)'
    )
    
    if (!confirmed) return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/emergency-stop`, {
        reason: reason || 'Emergency stop activated',
        message: `Emergency stop activated: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Fermata di emergenza attivata con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation, status: 'STOPPED' })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nell\'attivazione della fermata di emergenza'}`)
      }
    } catch (error) {
      console.error('Failed to activate emergency stop:', error)
      alert(`Errore nell'attivazione: ${error.response?.data?.error || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleResumeConversation = async () => {
    if (!isActionAvailable('resume')) {
      alert('Questa azione non è disponibile per conversazioni in stato ' + currentStatus)
      return
    }

    const reason = window.prompt('Inserisci il motivo per riprendere la conversazione:', '')
    if (reason === null || reason === '') return
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversation.id}/resume`, {
        reason: reason || 'Conversation resumed by operator',
        message: `Conversation resumed: ${reason || 'No reason provided'}`
      })
      
      if (response.data.success) {
        alert('Conversazione ripresa con successo')
        if (onConversationUpdated) {
          onConversationUpdated({ ...conversation, status: 'ACTIVE' })
        }
        onClose()
      } else {
        alert(`Errore: ${response.data.error || 'Errore nella ripresa della conversazione'}`)
      }
    } catch (error) {
      console.error('Failed to resume conversation:', error)
      alert(`Errore nella ripresa: ${error.response?.data?.error || error.message}`)
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
        let message = 'Allarme marcato come non attendibile'
        
        // Show warning if Kafka failed but operation succeeded
        if (response.data.warning) {
          message += `\n\n⚠️ Avviso: ${response.data.warning}`
        }
        
        alert(message)
        
        // Update conversation situation
        const updatedConversation = {
          ...conversation,
          situation: 'Regolare',
          situationLevel: 'low',
          risk_level: 'LOW',
          requires_attention: false
        }
        
        if (onConversationUpdated) {
          onConversationUpdated(updatedConversation)
        }
        
        onClose()
      } else {
        // Show specific error message from backend
        const errorMessage = response.data.message || response.data.error || 'Errore nel marcare l\'allarme come non attendibile'
        alert(`Errore nel marcare l'allarme come non attendibile:\n${errorMessage}`)
      }
    } catch (error) {
      console.error('Failed to mark alarm as unreliable:', error)
      
      // Show detailed error message
      let errorMessage = 'Errore nel marcare l\'allarme come non attendibile'
      if (error.response?.data?.message) {
        errorMessage += `\n${error.response.data.message}`
      } else if (error.response?.data?.error) {
        errorMessage += `\n${error.response.data.error}`
      } else if (error.message) {
        errorMessage += `\n${error.message}`
      }
      
      alert(errorMessage)
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

  const getStatusColor = (status) => {
    if (!status) return '#1976d2' // Default blue
    
    const statusUpper = status.toUpperCase()
    
    // Successfully completed - Green
    if (statusUpper === 'TERMINATED' || statusUpper === 'COMPLETED') {
      return '#059669' // Green
    }
    
    // Stopped unexpectedly - Red/Orange
    if (statusUpper === 'STOPPED') {
      return '#dc2626' // Red
    }
    
    // Cancelled - Gray
    if (statusUpper === 'CANCELLED' || statusUpper === 'CANCELED') {
      return '#6b7280' // Gray
    }
    
    // Active/In Progress - Blue
    if (statusUpper === 'IN_PROGRESS' || statusUpper === 'ACTIVE') {
      return '#1976d2' // Blue
    }
    
    // Default - Blue
    return '#1976d2'
  }

  const createdDate = formatDateTime(
    displayConversation.created_at || 
    displayConversation.createdAt || 
    displayConversation.session_start
  )
  const situationConfig = getSituationConfig(displayConversation.situation, displayConversation.situationLevel)
  const patientIdentifier = displayConversation.patientId || displayConversation.patient_id || displayConversation.id
  const patientName = displayConversation.patientInfo?.name 
    ? displayConversation.patientInfo.name 
    : t('conversationList.patientLabel', { id: patientIdentifier })
  const patientAgeRaw = displayConversation.patientInfo?.age
  const patientAgeLabel = patientAgeRaw && patientAgeRaw !== 0
    ? t('conversationDetail.patient.ageValue', { count: patientAgeRaw })
    : t('conversationDetail.patient.notAvailable')
  const patientGenderRaw = displayConversation.patientInfo?.gender
  const patientGenderLabel = patientGenderRaw && patientGenderRaw !== 'U' && patientGenderRaw !== null
    ? (patientGenderRaw === 'M'
        ? t('conversationList.gender.male')
        : patientGenderRaw === 'F'
          ? t('conversationList.gender.female')
          : patientGenderRaw)
    : t('conversationDetail.patient.notAvailable')
  const patientConditionLabel = displayConversation.patientInfo?.pathology && displayConversation.patientInfo.pathology !== 'Unknown' && displayConversation.patientInfo.pathology !== null
    ? displayConversation.patientInfo.pathology
    : t('conversationDetail.patient.notAvailable')
  const durationMinutes = displayConversation.duration || displayConversation.session_duration_minutes || 0
  const sessionHeading = t('conversationDetail.session.heading', { date: createdDate.date })
  const sessionSummary = t('conversationDetail.session.summary', {
    time: createdDate.time,
    status: displayConversation.status,
    duration: durationMinutes
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="conversation-detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <h2>{t('conversationDetail.title')}</h2>
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
              <h3>{patientName}</h3>
              <div className="patient-meta">
                <span>{`${t('conversationDetail.patient.age')}: ${patientAgeLabel}`}</span>
                <span>{`${t('conversationDetail.patient.gender')}: ${patientGenderLabel}`}</span>
                <span>{`${t('conversationDetail.patient.condition')}: ${patientConditionLabel}`}</span>
              </div>
            </div>
          </div>
          
          <div className="conversation-info">
            <h4>{sessionHeading}</h4>
            <p>
              {t('conversationDetail.session.summary', { time: createdDate.time })}{' '}
              <span className="status-text" style={{ color: getStatusColor(displayConversation.status) }}>
                {displayConversation.status}
              </span>
              {t('conversationDetail.session.duration', { duration: durationMinutes })}
            </p>
          </div>
        </div>

        {/* Alert Box */}
        {situationConfig.class !== 'situation-regular' && (
          <div className={`alert-box ${situationConfig.class}`}>
            <div className="alert-icon">{situationConfig.icon}</div>
            <div className="alert-content">
              <h4>{situationConfig.label}</h4>
              <p>{situationConfig.description}</p>
            </div>
          </div>
        )}

        {/* Action History Toggle */}
        {recentActions.length > 0 && (
          <div className="action-history-toggle" style={{ padding: '0 2rem 1rem 2rem' }}>
            <button
              onClick={() => setShowActionHistory(!showActionHistory)}
              className="btn-history-toggle"
            >
              {t('conversationDetail.history.toggle', {
                icon: showActionHistory ? '▼' : '▶',
                count: recentActions.length
              })}
            </button>
          </div>
        )}

        {/* Action History Display */}
        {showActionHistory && recentActions.length > 0 && (
          <div className="action-history" style={{ padding: '0 2rem 1.5rem 2rem', marginBottom: '1rem', borderBottom: '1px solid #f1f3f4' }}>
            <h4>{t('conversationDetail.history.title')}</h4>
            <div className="action-history-list">
              {recentActions.slice(0, 10).map((action, idx) => {
                const actionTime = formatDateTime(action.timestamp)
                return (
                  <div key={action.id || idx} className="action-history-item">
                    <div className="action-history-time">
                      {actionTime.date} {actionTime.time}
                    </div>
                    <div className="action-history-content">
                      <strong>{action.type || t('conversationDetail.history.defaultAction')}</strong> - {action.description || t('conversationDetail.history.noDescription')}
                      {action.operator && (
                        <span className="action-history-operator">
                          {t('conversationDetail.history.operator', { name: action.operator })}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Action Buttons - Grouped by Category */}
        <div className="action-buttons-container">
          {/* Lifecycle Actions */}
          <div className="action-button-group">
            <div className="action-group-header">
              <span className="action-group-title">{sectionTitles.lifecycle}</span>
            </div>
        <div className="action-buttons">
          <button 
            className="btn-stop-report"
            onClick={handleStopAndReport}
                disabled={loading || !isActionAvailable('stop')}
                title={actionTooltips.stopReport}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                <span className="btn-icon">🛑</span>
                {actionLabels.stopReport}
              </>
            )}
          </button>
          
          <button 
            className="btn-complete"
            onClick={handleCompleteConversation}
                disabled={loading || !isActionAvailable('complete')}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                <span className="btn-icon">✅</span>
                {actionLabels.complete}
              </>
            )}
          </button>
          
          <button 
                className="btn-cancel"
                onClick={handleCancelConversation}
                disabled={loading || !isActionAvailable('cancel')}
          >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    {processingText}
                  </>
                ) : (
                  <>
                    <span className="btn-icon">❌</span>
                    {actionLabels.cancel}
                  </>
                )}
          </button>
          
              <button 
                className="btn-resume"
                onClick={handleResumeConversation}
                disabled={loading || !isActionAvailable('resume')}
                title={actionTooltips.resume}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    {processingText}
                  </>
                ) : (
                  <>
                    <span className="btn-icon">▶️</span>
                    {actionLabels.resume}
                  </>
                )}
              </button>
              
              <button 
                className="btn-emergency-stop"
                onClick={handleEmergencyStop}
                disabled={loading || !isActionAvailable('emergency_stop')}
                title={actionTooltips.emergencyStop}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    {processingText}
                  </>
                ) : (
                  <>
                    <span className="btn-icon">🚨</span>
                    {actionLabels.emergencyStop}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Escalation & Attention Actions */}
          <div className="action-button-group">
            <div className="action-group-header">
              <span className="action-group-title">{sectionTitles.escalation}</span>
            </div>
            <div className="action-buttons">
          <button 
            className="btn-escalate"
            onClick={handleEscalate}
                disabled={loading || !isActionAvailable('escalate')}
                title={actionTooltips.escalate}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                <span className="btn-icon">⬆️</span>
                    {actionLabels.escalate}
                  </>
                )}
              </button>
              
              <button 
                className="btn-manual-intervention"
                onClick={handleManualIntervention}
                disabled={loading || !isActionAvailable('manual_intervention')}
                title={actionTooltips.manualIntervention}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    {processingText}
                  </>
                ) : (
                  <>
                    <span className="btn-icon">👋</span>
                    {actionLabels.manualIntervention}
              </>
            )}
          </button>
          
          <button 
            className="btn-acknowledge"
            onClick={handleAcknowledge}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                <span className="btn-icon">✓</span>
                {actionLabels.acknowledge}
              </>
            )}
          </button>
          
          <button 
            className="btn-resolve"
            onClick={handleResolve}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                <span className="btn-icon">✅</span>
                {actionLabels.resolve}
              </>
            )}
          </button>
            </div>
          </div>

          {/* System Control Actions */}
          <div className="action-button-group">
            <div className="action-group-header">
              <span className="action-group-title">{sectionTitles.system}</span>
            </div>
            <div className="action-buttons">
          <button 
                className="btn-override-guardrail"
                onClick={handleOverrideGuardrail}
            disabled={loading}
                title={actionTooltips.overrideGuardrail}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {processingText}
              </>
            ) : (
              <>
                    <span className="btn-icon">🔄</span>
                    {actionLabels.overrideGuardrail}
              </>
            )}
          </button>
              
              <button 
                className="btn-system-override"
                onClick={handleSystemOverride}
                disabled={loading}
                title={actionTooltips.systemOverride}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    {processingText}
                  </>
                ) : (
                  <>
                    <span className="btn-icon">⚙️</span>
                    {actionLabels.systemOverride}
                  </>
                )}
              </button>
              
              <button 
                className="btn-unreliable-alarm"
                onClick={handleUnreliableAlarm}
                disabled={loading}
              >
                <span className="btn-icon">👤</span>
                {actionLabels.unreliableAlarm}
              </button>
            </div>
          </div>
        </div>

        {/* Conversation Report */}
        <div className="conversation-report">
          <h4>{sectionTitles.report}</h4>
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
                {generatingReport ? reportGenerating : reportPdf}
              </span>
            </div>
          </div>
        </div>

        {/* Event Log */}
        <div className="event-log">
          <h4>{sectionTitles.events}</h4>
          <div className="event-table-container">
            <table className="event-table">
              <thead>
                <tr>
                  <th>{eventTableHeaders.event}</th>
                  <th>{eventTableHeaders.description}</th>
                  <th>{eventTableHeaders.details}</th>
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
                          {event.description || event.message_content || event.message || eventTableHeaders.noDescription}
                        </td>
                        <td className="event-details">
                          {formatEventDetails(event.details || event.context)}
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan="3" className="no-events">
                      {eventTableHeaders.none}
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
            <span className="alternative-label">{sectionTitles.alternative}</span>
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
