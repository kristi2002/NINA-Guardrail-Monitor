import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ConversationDetailModal from './ConversationDetailModal'
import CustomSelect from './CustomSelect'
import flatpickr from 'flatpickr'
import 'flatpickr/dist/flatpickr.min.css'
import { Italian } from 'flatpickr/dist/l10n/it'
import './ConversationList.css'

function ConversationList({ conversations = [], onConversationsRefresh }) {
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [openDropdownId, setOpenDropdownId] = useState(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  
  // Filter states
  const [filterSearch, setFilterSearch] = useState('') // Patient ID - first
  const [filterStatus, setFilterStatus] = useState('all') // Status - second
  const [filterSituation, setFilterSituation] = useState('all') // Situation - third
  const [filterDateFrom, setFilterDateFrom] = useState('') // Creation Date From
  const [filterDateTo, setFilterDateTo] = useState('') // Creation Date To
  const [filterUpdatedFrom, setFilterUpdatedFrom] = useState('') // Last Update From
  const [filterUpdatedTo, setFilterUpdatedTo] = useState('') // Last Update To

  const getStatusConfig = (status) => {
    const configs = {
      'NEW': { label: 'Nuova', class: 'status-new', icon: '🆕' },
      'IN_PROGRESS': { label: 'In corso', class: 'status-in-progress', icon: '⚙️' },
      'STOPPED': { label: 'Fermata', class: 'status-stopped', icon: '⏹️' },
      'CANCELLED': { label: 'Annullata', class: 'status-cancelled', icon: '❌' },
      'COMPLETED': { label: 'Terminata', class: 'status-completed', icon: '✅' }
    }
    return configs[status] || configs['NEW']
  }

  const getSituationConfig = (situation, level) => {
    const configs = {
      'Regolare': { 
        label: 'Regolare', 
        class: 'situation-regular', 
        icon: '👍',
        color: '#51cf66'
      },
      'Segni di autolesionismo': { 
        label: 'Segni di autolesionismo', 
        class: 'situation-warning', 
        icon: '⚠️',
        color: '#ffa726'
      },
      'Gesti pericolosi': { 
        label: 'Gesti pericolosi', 
        class: 'situation-danger', 
        icon: '🚨',
        color: '#f44336'
      }
    }
    
    // If situation text matches a known config, use it
    if (situation && configs[situation]) {
      return configs[situation]
    }
    
    // Otherwise, use risk level to determine situation
    const normalizedLevel = (level || 'low').toLowerCase()
    if (normalizedLevel === 'high' || normalizedLevel === 'critical') {
      return configs['Gesti pericolosi']
    } else if (normalizedLevel === 'medium') {
      return configs['Segni di autolesionismo']
    } else {
      return configs['Regolare']
    }
  }

  // Use conversations from props (from API)
  const allConversations = Array.isArray(conversations) ? conversations : []
  
  // Apply filters
  const displayConversations = allConversations.filter(conversation => {
    // Safety check: skip invalid conversations
    if (!conversation || typeof conversation !== 'object') {
      return false
    }
    
    try {
      // Search filter (patient ID) - first
      if (filterSearch && filterSearch.trim() !== '') {
        const searchTerm = filterSearch.toLowerCase()
        const patientId = (conversation.patientId || conversation.id || '').toString().toLowerCase()
        if (!patientId.includes(searchTerm)) {
          return false
        }
      }
      
      // Status filter - second
      if (filterStatus !== 'all' && conversation.status !== filterStatus) {
        return false
      }
      
      // Situation filter - third
      if (filterSituation !== 'all') {
        const situationConfig = getSituationConfig(conversation.situation, conversation.situationLevel)
        if (filterSituation === 'regular' && situationConfig.class !== 'situation-regular') {
          return false
        }
        if (filterSituation === 'warning' && situationConfig.class !== 'situation-warning') {
          return false
        }
        if (filterSituation === 'danger' && situationConfig.class !== 'situation-danger') {
          return false
        }
      }
      
      // Creation date filter
      if (filterDateFrom || filterDateTo) {
        const createdDate = conversation.created_at || conversation.createdAt || conversation.session_start
        if (createdDate) {
          const convDate = new Date(createdDate)
          if (isNaN(convDate.getTime())) {
            // Invalid date, exclude if filters are set
            if (filterDateFrom || filterDateTo) {
              return false
            }
          } else {
            if (filterDateFrom) {
              // Convert DD/MM/YYYY to YYYY-MM-DD if needed
              let fromDateStr = filterDateFrom
              if (filterDateFrom.includes('/')) {
                const [day, month, year] = filterDateFrom.split('/')
                fromDateStr = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
              }
              const fromDate = new Date(fromDateStr)
              if (!isNaN(fromDate.getTime())) {
                fromDate.setHours(0, 0, 0, 0)
                if (convDate < fromDate) {
                  return false
                }
              }
            }
            if (filterDateTo) {
              // Convert DD/MM/YYYY to YYYY-MM-DD if needed
              let toDateStr = filterDateTo
              if (filterDateTo.includes('/')) {
                const [day, month, year] = filterDateTo.split('/')
                toDateStr = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
              }
              const toDate = new Date(toDateStr)
              if (!isNaN(toDate.getTime())) {
                toDate.setHours(23, 59, 59, 999)
                if (convDate > toDate) {
                  return false
                }
              }
            }
          }
        } else {
          // If no creation date and filters are set, exclude
          if (filterDateFrom || filterDateTo) {
            return false
          }
        }
      }
      
      // Last update date filter
      if (filterUpdatedFrom || filterUpdatedTo) {
        const updatedDate = conversation.updated_at || conversation.lastUpdated || conversation.session_end
        if (updatedDate) {
          const convDate = new Date(updatedDate)
          if (isNaN(convDate.getTime())) {
            // Invalid date, exclude if filters are set
            if (filterUpdatedFrom || filterUpdatedTo) {
              return false
            }
          } else {
            if (filterUpdatedFrom) {
              // Convert DD/MM/YYYY to YYYY-MM-DD if needed
              let fromDateStr = filterUpdatedFrom
              if (filterUpdatedFrom.includes('/')) {
                const [day, month, year] = filterUpdatedFrom.split('/')
                fromDateStr = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
              }
              const fromDate = new Date(fromDateStr)
              if (!isNaN(fromDate.getTime())) {
                fromDate.setHours(0, 0, 0, 0)
                if (convDate < fromDate) {
                  return false
                }
              }
            }
            if (filterUpdatedTo) {
              // Convert DD/MM/YYYY to YYYY-MM-DD if needed
              let toDateStr = filterUpdatedTo
              if (filterUpdatedTo.includes('/')) {
                const [day, month, year] = filterUpdatedTo.split('/')
                toDateStr = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
              }
              const toDate = new Date(toDateStr)
              if (!isNaN(toDate.getTime())) {
                toDate.setHours(23, 59, 59, 999)
                if (convDate > toDate) {
                  return false
                }
              }
            }
          }
        } else {
          // If no update date and filters are set, exclude
          if (filterUpdatedFrom || filterUpdatedTo) {
            return false
          }
        }
      }
      
      return true
    } catch (error) {
      console.error('Error filtering conversation:', error, conversation)
      return false
    }
  })
  
  // Reset filters
  const resetFilters = () => {
    setFilterSearch('')
    setFilterStatus('all')
    setFilterSituation('all')
    setFilterDateFrom('')
    setFilterDateTo('')
    setFilterUpdatedFrom('')
    setFilterUpdatedTo('')
    // Clear Flatpickr instances
    if (dateFromRef.current && dateFromRef.current._flatpickr) {
      dateFromRef.current._flatpickr.clear()
    }
    if (dateToRef.current && dateToRef.current._flatpickr) {
      dateToRef.current._flatpickr.clear()
    }
    if (updatedFromRef.current && updatedFromRef.current._flatpickr) {
      updatedFromRef.current._flatpickr.clear()
    }
    if (updatedToRef.current && updatedToRef.current._flatpickr) {
      updatedToRef.current._flatpickr.clear()
    }
  }
  
  // Count active filters
  const activeFiltersCount = 
    (filterSearch.trim() !== '' ? 1 : 0) +
    (filterStatus !== 'all' ? 1 : 0) +
    (filterSituation !== 'all' ? 1 : 0) +
    (filterDateFrom !== '' ? 1 : 0) +
    (filterDateTo !== '' ? 1 : 0) +
    (filterUpdatedFrom !== '' ? 1 : 0) +
    (filterUpdatedTo !== '' ? 1 : 0)

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

  const handleConversationClick = (conversation) => {
    setSelectedConversation(conversation)
    setShowDetailModal(true)
  }

  const handleStopAndReport = async (conversationId) => {
    // Confirm before stopping
    const confirmed = window.confirm(
      'Sei sicuro di voler fermare e segnalare questa conversazione?\n\n' +
      'Questa azione fermerà la conversazione e la segnalerà come interrotta dall\'amministratore.'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversationId}/stop`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        let message = 'Conversazione fermata e segnalata con successo'
        
        // Show warning if Kafka failed but action succeeded
        if (response.data.warning) {
          message += `\n\n⚠️ Avviso: ${response.data.warning}`
        }
        
        alert(message)
        if (onConversationsRefresh) {
          onConversationsRefresh()
        }
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

  const handleCompleteConversation = async (conversationId) => {
    // Confirm before completing
    const confirmed = window.confirm(
      'Sei sicuro di voler completare questa conversazione?\n\n' +
      'Questa azione segnerà la conversazione come completata.'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversationId}/complete`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Conversazione completata con successo')
        if (onConversationsRefresh) {
          onConversationsRefresh()
        }
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

  const handleActionMenu = (conversationId, action) => {
    setOpenDropdownId(null) // Close dropdown after action
    switch (action) {
      case 'stop':
        handleStopAndReport(conversationId)
        break
      case 'complete':
        handleCompleteConversation(conversationId)
        break
      default:
        console.log('Unknown action:', action)
    }
  }

  const toggleDropdown = (conversationId, e) => {
    e.stopPropagation()
    setOpenDropdownId(openDropdownId === conversationId ? null : conversationId)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.action-dropdown')) {
        setOpenDropdownId(null)
      }
    }

    if (openDropdownId) {
      document.addEventListener('click', handleClickOutside)
      return () => {
        document.removeEventListener('click', handleClickOutside)
      }
    }
  }, [openDropdownId])

  // Initialize Flatpickr for date inputs
  const dateFromRef = useRef(null)
  const dateToRef = useRef(null)
  const updatedFromRef = useRef(null)
  const updatedToRef = useRef(null)

  useEffect(() => {
    if (!filtersOpen) return

    // Helper to convert YYYY-MM-DD to DD/MM/YYYY for Flatpickr
    const formatForFlatpickr = (dateStr) => {
      if (!dateStr) return ''
      if (dateStr.includes('/')) return dateStr // Already in DD/MM/YYYY format
      if (dateStr.includes('-')) {
        const [year, month, day] = dateStr.split('-')
        return `${day}/${month}/${year}`
      }
      return dateStr
    }

    const fpOptions = {
      dateFormat: 'd/m/Y',
      locale: Italian,
      allowInput: true,
      clickOpens: true,
      placeholder: 'gg/mm/aaaa',
    }

    const fp1 = dateFromRef.current ? flatpickr(dateFromRef.current, {
      ...fpOptions,
      defaultDate: formatForFlatpickr(filterDateFrom),
      onChange: (selectedDates, dateStr) => {
        setFilterDateFrom(dateStr || '')
      }
    }) : null

    const fp2 = dateToRef.current ? flatpickr(dateToRef.current, {
      ...fpOptions,
      defaultDate: formatForFlatpickr(filterDateTo),
      onChange: (selectedDates, dateStr) => {
        setFilterDateTo(dateStr || '')
      }
    }) : null

    const fp3 = updatedFromRef.current ? flatpickr(updatedFromRef.current, {
      ...fpOptions,
      defaultDate: formatForFlatpickr(filterUpdatedFrom),
      onChange: (selectedDates, dateStr) => {
        setFilterUpdatedFrom(dateStr || '')
      }
    }) : null

    const fp4 = updatedToRef.current ? flatpickr(updatedToRef.current, {
      ...fpOptions,
      defaultDate: formatForFlatpickr(filterUpdatedTo),
      onChange: (selectedDates, dateStr) => {
        setFilterUpdatedTo(dateStr || '')
      }
    }) : null

    return () => {
      if (fp1) fp1.destroy()
      if (fp2) fp2.destroy()
      if (fp3) fp3.destroy()
      if (fp4) fp4.destroy()
    }
  }, [filtersOpen, filterDateFrom, filterDateTo, filterUpdatedFrom, filterUpdatedTo])

  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <h3>Monitoraggio conversazioni</h3>
        <div className="conversation-stats">
          <span className="total-conversations">{displayConversations.length || 0} conversazioni</span>
          <span className="active-conversations">
            {displayConversations.filter(c => c && c.status === 'IN_PROGRESS').length || 0} attive
          </span>
        </div>
      </div>

      {/* Filters Section */}
      <div className="filters-section">
        <button 
          className="filters-toggle"
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <span className="filter-icon">🔍</span>
          <span>Filtri</span>
          {activeFiltersCount > 0 && (
            <span className="filter-badge">{activeFiltersCount}</span>
          )}
          <span className={`toggle-arrow ${filtersOpen ? 'open' : ''}`}>▼</span>
        </button>
        
        <div className={`filters-content ${filtersOpen ? 'open' : ''}`}>
            <div className="filters-grid">
              {/* Paziente - First column */}
              <div className="filter-group">
                <label className="filter-label">Cerca Paziente (ID)</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder="Inserisci ID paziente..."
                  value={filterSearch}
                  onChange={(e) => setFilterSearch(e.target.value)}
                />
              </div>
              
              {/* Stato - Second column */}
              <div className="filter-group">
                <label className="filter-label">Stato</label>
                <CustomSelect
                  className="filter-select"
                  value={filterStatus}
                  onChange={setFilterStatus}
                  placeholder="Tutti"
                  options={[
                    { value: 'all', label: 'Tutti' },
                    { value: 'IN_PROGRESS', label: 'In corso' },
                    { value: 'COMPLETED', label: 'Terminata' },
                    { value: 'STOPPED', label: 'Fermata' },
                    { value: 'NEW', label: 'Nuova' },
                    { value: 'CANCELLED', label: 'Annullata' }
                  ]}
                />
              </div>
              
              {/* Situazione - Third column */}
              <div className="filter-group">
                <label className="filter-label">Situazione</label>
                <CustomSelect
                  className="filter-select"
                  value={filterSituation}
                  onChange={setFilterSituation}
                  placeholder="Tutte"
                  options={[
                    { value: 'all', label: 'Tutte' },
                    { value: 'regular', label: 'Regolare' },
                    { value: 'warning', label: 'Segni di autolesionismo' },
                    { value: 'danger', label: 'Gesti pericolosi' }
                  ]}
                />
              </div>
              
              {/* Data Creazione - Fourth column */}
              <div className="filter-group" lang="it-IT">
                <label className="filter-label">Data Creazione Da</label>
                <input
                  type="text"
                  ref={dateFromRef}
                  className="filter-input"
                  placeholder="gg/mm/aaaa"
                  data-input
                />
              </div>
              
              <div className="filter-group" lang="it-IT">
                <label className="filter-label">Data Creazione A</label>
                <input
                  type="text"
                  ref={dateToRef}
                  className="filter-input"
                  placeholder="gg/mm/aaaa"
                  data-input
                />
              </div>
              
              {/* Ultimo Aggiornamento - Fifth column */}
              <div className="filter-group" lang="it-IT">
                <label className="filter-label">Ultimo Aggiornamento Da</label>
                <input
                  type="text"
                  ref={updatedFromRef}
                  className="filter-input"
                  placeholder="gg/mm/aaaa"
                  data-input
                />
              </div>
              
              <div className="filter-group" lang="it-IT">
                <label className="filter-label">Ultimo Aggiornamento A</label>
                <input
                  type="text"
                  ref={updatedToRef}
                  className="filter-input"
                  placeholder="gg/mm/aaaa"
                  data-input
                />
              </div>
              
              {/* Reset button - in same grid */}
              <div className="filter-group filter-actions">
                <button 
                  className="btn-reset-filters"
                  onClick={resetFilters}
                  disabled={activeFiltersCount === 0}
                >
                  <span className="reset-icon">↺</span>
                  Reset filtri
                </button>
              </div>
            </div>
          </div>
      </div>

      <div className="conversation-table-container">
        {displayConversations.length === 0 ? (
          <div className="conversation-list-empty">
            <div className="empty-icon"></div>
            <div className="empty-text">Nessun risultato trovato</div>
            <div className="empty-subtext">
              {activeFiltersCount > 0 
                ? 'Nessuna conversazione corrisponde ai filtri selezionati. Prova a modificare i criteri di ricerca.'
                : 'Il sistema è in attesa di nuove conversazioni'}
            </div>
          </div>
        ) : (
          <table className="conversation-table">
            <thead>
              <tr>
                <th>Paziente</th>
                <th>Stato</th>
                <th>Situazione</th>
                <th>Data Creazione</th>
                <th>Ultimo aggiornamento</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {displayConversations.map((conversation) => {
              if (!conversation || !conversation.id) {
                return null
              }
              
              try {
              const statusConfig = getStatusConfig(conversation.status || 'NEW')
              const situationConfig = getSituationConfig(conversation.situation, conversation.situationLevel)
              const createdDate = formatDateTime(
                conversation.created_at || 
                conversation.createdAt || 
                conversation.session_start
              )
              const updatedDate = formatDateTime(
                conversation.updated_at || 
                conversation.lastUpdated || 
                conversation.session_end
              )

              return (
                <tr 
                  key={conversation.id}
                  className={`conversation-row ${conversation.situationLevel === 'high' ? 'high-risk' : ''} ${openDropdownId === conversation.id ? 'dropdown-open' : ''}`}
                  onClick={() => handleConversationClick(conversation)}
                >
                  <td className="patient-cell">
                    <div className="patient-info">
                      <div className="patient-avatar">
                        <span className="patient-icon">👤</span>
                        {conversation.id === 1 && <span className="patient-badge">1</span>}
                      </div>
                      <div className="patient-details">
                        <div className="patient-name">
                          {conversation.patientId ? `Paziente ${conversation.patientId}` : `Paziente ${conversation.id}`}
                        </div>
                        <div className="patient-meta">
                          {conversation.patientInfo?.age || 'N/A'} anni, {(conversation.patientInfo?.gender && conversation.patientInfo.gender !== 'U' && conversation.patientInfo.gender !== null) ? conversation.patientInfo.gender : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="status-cell">
                    <span className={`status-badge ${statusConfig.class}`}>
                      {statusConfig.icon} {statusConfig.label}
                    </span>
                  </td>
                  
                  <td className="situation-cell">
                    <span 
                      className={`situation-badge ${situationConfig.class}`}
                    >
                      {situationConfig.icon} {situationConfig.label}
                    </span>
                  </td>
                  
                  <td className="date-cell">
                    <div className="date-info">
                      <span className="date-icon">📅</span>
                      <span className="date-text">{createdDate.date}, {createdDate.time}</span>
                    </div>
                  </td>
                  
                  <td className="date-cell">
                    <div className="date-info">
                      <span className="date-icon">📅</span>
                      <span className="date-text">{updatedDate.date}, {updatedDate.time}</span>
                    </div>
                  </td>
                  
                  <td className="actions-cell">
                    <div className="action-dropdown">
                      <button 
                        className="action-button"
                        onClick={(e) => toggleDropdown(conversation.id, e)}
                      >
                        <span className="action-icon">▼</span>
                        Azioni
                      </button>
                      {openDropdownId === conversation.id && (
                        <div className="action-dropdown-menu">
                          <button
                            className="action-menu-item"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleActionMenu(conversation.id, 'stop')
                            }}
                          >
                            <span className="menu-icon">⏹️</span>
                            Ferma e segnala
                          </button>
                          <button
                            className="action-menu-item"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleActionMenu(conversation.id, 'complete')
                            }}
                          >
                            <span className="menu-icon">✅</span>
                            Completa conversazione
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              )
              } catch (error) {
                console.error('Error rendering conversation row:', error, conversation)
                return null
              }
            }).filter(Boolean)}
          </tbody>
        </table>
        )}
      </div>

      {/* Conversation Detail Modal */}
      <ConversationDetailModal
        conversation={selectedConversation}
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false)
          setSelectedConversation(null)
        }}
        onConversationUpdated={(updatedConversation) => {
          console.log('Conversation updated:', updatedConversation)
          if (onConversationsRefresh) {
            onConversationsRefresh()
          }
        }}
      />
    </div>
  )
}

export default ConversationList
