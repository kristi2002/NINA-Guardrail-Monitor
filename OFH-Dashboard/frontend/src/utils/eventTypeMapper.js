/**
 * Event Type Mapper
 * Maps backend event types to frontend display categories
 */

/**
 * Maps backend event_type to frontend display type
 * @param {string} eventType - Backend event_type (e.g., 'conversation_started', 'privacy_violation_prevented')
 * @param {string} severity - Backend severity (info, medium, high, critical)
 * @returns {string} Frontend display type (INFO, WARNING, ALERT)
 */
export function mapEventTypeToDisplay(eventType, severity) {
  // Info level events
  const infoTypes = [
    'conversation_started',
    'conversation_ended',
    'validation_passed'
  ]
  
  // Warning level events
  const warningTypes = [
    'warning_triggered',
    'inappropriate_content',
    'compliance_check'
  ]
  
  // Alert level events
  const alertTypes = [
    'alarm_triggered',
    'privacy_violation_prevented',
    'medication_warning',
    'emergency_protocol',
    'operator_intervention',
    'system_alert',
    'validation_failed',
    'persistent_evasion',
    'jailbreak_attempt',
    'security_bypass_attempt'
  ]
  
  // Convert severity to display type if event_type not recognized
  if (!eventType) {
    if (severity === 'critical' || severity === 'high') return 'ALERT'
    if (severity === 'medium') return 'WARNING'
    return 'INFO'
  }
  
  eventType = eventType.toLowerCase()
  
  if (infoTypes.includes(eventType)) return 'INFO'
  if (warningTypes.includes(eventType)) return 'WARNING'
  if (alertTypes.includes(eventType)) return 'ALERT'
  
  // Fallback based on severity
  return mapSeverityToDisplay(severity)
}

/**
 * Maps backend severity to frontend display type
 * @param {string} severity - Backend severity (info, medium, high, critical)
 * @returns {string} Frontend display type (INFO, WARNING, ALERT)
 */
export function mapSeverityToDisplay(severity) {
  if (!severity) return 'INFO'
  
  severity = severity.toLowerCase()
  
  if (severity === 'critical' || severity === 'high') return 'ALERT'
  if (severity === 'medium') return 'WARNING'
  return 'INFO'
}

/**
 * Gets human-readable label for backend event type
 * @param {string} eventType - Backend event_type
 * @returns {string} Human-readable label
 */
export function getEventTypeLabel(eventType) {
  const labels = {
    'conversation_started': 'Conversazione Avviata',
    'conversation_ended': 'Conversazione Terminata',
    'validation_passed': 'Validazione Passata',
    'warning_triggered': 'Avviso Attivato',
    'inappropriate_content': 'Contenuto Inappropriato',
    'compliance_check': 'Controllo Compliance',
    'alarm_triggered': 'Allarme Attivato',
    'privacy_violation_prevented': 'Violazione Privacy Bloccata',
    'medication_warning': 'Avviso Farmaceutico',
    'emergency_protocol': 'Protocollo di Emergenza',
    'operator_intervention': 'Intervento Operatore',
    'system_alert': 'Allarme Sistema',
    'validation_failed': 'Validazione Fallita',
    'false_alarm_reported': 'Falso Allarme Segnalato',
    'persistent_evasion': 'Tentativo di Evasione Persistente',
    'jailbreak_attempt': 'Tentativo di Jailbreak',
    'security_bypass_attempt': 'Tentativo di Bypass Sicurezza'
  }
  
  return labels[eventType] || eventType
}

/**
 * Gets icon for backend event type
 * @param {string} eventType - Backend event_type
 * @returns {string} Icon emoji
 */
export function getEventTypeIcon(eventType) {
  const icons = {
    'conversation_started': '💬',
    'conversation_ended': '✅',
    'validation_passed': '✓',
    'warning_triggered': '⚠️',
    'inappropriate_content': '🚫',
    'compliance_check': '📋',
    'alarm_triggered': '🚨',
    'privacy_violation_prevented': '🔒',
    'medication_warning': '💊',
    'emergency_protocol': '🆘',
    'operator_intervention': '👤',
    'system_alert': '⚠️',
    'validation_failed': '❌',
    'false_alarm_reported': '✓',
    'persistent_evasion': '🛡️',
    'jailbreak_attempt': '🔓',
    'security_bypass_attempt': '🚫'
  }
  
  return icons[eventType] || 'ℹ️'
}

/**
 * Gets color for backend event type
 * @param {string} eventType - Backend event_type
 * @returns {object} Color configuration { color, bgColor }
 */
export function getEventTypeColor(eventType) {
  const colors = {
    'conversation_started': { color: '#1976d2', bgColor: '#e3f2fd' },
    'conversation_ended': { color: '#4caf50', bgColor: '#e8f5e9' },
    'validation_passed': { color: '#4caf50', bgColor: '#e8f5e9' },
    'warning_triggered': { color: '#f57c00', bgColor: '#fff3e0' },
    'inappropriate_content': { color: '#f57c00', bgColor: '#fff3e0' },
    'compliance_check': { color: '#f57c00', bgColor: '#fff3e0' },
    'alarm_triggered': { color: '#d32f2f', bgColor: '#ffebee' },
    'privacy_violation_prevented': { color: '#d32f2f', bgColor: '#ffebee' },
    'medication_warning': { color: '#d32f2f', bgColor: '#ffebee' },
    'emergency_protocol': { color: '#d32f2f', bgColor: '#ffebee' },
    'operator_intervention': { color: '#1976d2', bgColor: '#e3f2fd' },
    'system_alert': { color: '#f57c00', bgColor: '#fff3e0' },
    'validation_failed': { color: '#d32f2f', bgColor: '#ffebee' },
    'false_alarm_reported': { color: '#4caf50', bgColor: '#e8f5e9' },
    'persistent_evasion': { color: '#d32f2f', bgColor: '#ffebee' },
    'jailbreak_attempt': { color: '#d32f2f', bgColor: '#ffebee' },
    'security_bypass_attempt': { color: '#d32f2f', bgColor: '#ffebee' }
  }
  
  return colors[eventType] || { color: '#1976d2', bgColor: '#e3f2fd' }
}

export default {
  mapEventTypeToDisplay,
  mapSeverityToDisplay,
  getEventTypeLabel,
  getEventTypeIcon,
  getEventTypeColor
}

