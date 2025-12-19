import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import axios from 'axios'
import ConversationDetailModal from './ConversationDetailModal'
import { CustomSelect } from '../ui'
import flatpickr from 'flatpickr'
import 'flatpickr/dist/flatpickr.min.css'
import { Italian } from 'flatpickr/dist/l10n/it'
import { useTranslation } from 'react-i18next'
import './ConversationList.css'

function ConversationList({ conversations = [], onConversationsRefresh }) {
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [openDropdownId, setOpenDropdownId] = useState(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [sortConfig, setSortConfig] = useState({ key: 'default', direction: 'desc' })
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10
  
  // Filter states
  const [filterSearch, setFilterSearch] = useState('') // Patient ID - first
  const [filterPatientName, setFilterPatientName] = useState('') // Patient Name
  const [filterPatientLastName, setFilterPatientLastName] = useState('') // Patient Last Name
  const [filterStatus, setFilterStatus] = useState('all') // Status - second
  const [filterSituation, setFilterSituation] = useState('all') // Situation - third
  const [filterDateFrom, setFilterDateFrom] = useState('') // Creation Date From
  const [filterDateTo, setFilterDateTo] = useState('') // Creation Date To
  const [filterUpdatedFrom, setFilterUpdatedFrom] = useState('') // Last Update From
  const [filterUpdatedTo, setFilterUpdatedTo] = useState('') // Last Update To

  const { t, i18n } = useTranslation()

  const statusConfigs = useMemo(() => ({
    NEW: { label: t('conversationList.statusLabels.new'), class: 'status-new', icon: '🆕' },
    IN_PROGRESS: { label: t('conversationList.statusLabels.inProgress'), class: 'status-in-progress', icon: '⚙️' },
    STOPPED: { label: t('conversationList.statusLabels.stopped'), class: 'status-stopped', icon: '⏹️' },
    CANCELLED: { label: t('conversationList.statusLabels.cancelled'), class: 'status-cancelled', icon: '❌' },
    COMPLETED: { label: t('conversationList.statusLabels.completed'), class: 'status-completed', icon: '✅' }
  }), [t])

  const getStatusConfig = (status) => statusConfigs[status] || statusConfigs.NEW

  const situationConfigs = useMemo(() => ({
    regular: {
      label: t('conversationList.situationLabels.regular'),
      class: 'situation-regular',
      icon: '👍',
      color: '#51cf66'
    },
    warning: {
      label: t('conversationList.situationLabels.warning'),
      class: 'situation-warning',
      icon: '⚠️',
      color: '#ffa726'
    },
    danger: {
      label: t('conversationList.situationLabels.danger'),
      class: 'situation-danger',
      icon: '🚨',
      color: '#f44336'
    }
  }), [t])

  const getSituationConfig = (situation, level) => {
    // First check risk_level (most authoritative) - it takes priority over situation text
    const normalizedLevel = (level || 'low').toLowerCase()
    if (normalizedLevel === 'high' || normalizedLevel === 'critical') {
      return situationConfigs.danger
    }
    if (normalizedLevel === 'medium') {
      return situationConfigs.warning
    }

    // Then check situation text as fallback
    const normalizedSituation = (situation || '').toString().toLowerCase()

    if (normalizedSituation.includes('pericol') || normalizedSituation.includes('danger')) {
      return situationConfigs.danger
    }

    if (normalizedSituation.includes('autolesion') || normalizedSituation.includes('warning')) {
      return situationConfigs.warning
    }

    if (normalizedSituation.includes('regolar') || normalizedSituation.includes('regular')) {
      return situationConfigs.regular
    }

    // Default to regular if nothing matches
    return situationConfigs.regular
  }

  const genderLabels = useMemo(() => ({
    M: t('conversationList.gender.male'),
    F: t('conversationList.gender.female')
  }), [t])

  const getGenderLabel = (gender) => genderLabels[gender] || t('conversationList.gender.unknown')

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
      
      // Patient name filter
      if (filterPatientName && filterPatientName.trim() !== '') {
        const nameSearchTerm = filterPatientName.toLowerCase().trim()
        const patientName = (conversation.patientInfo?.name || '').toString().toLowerCase()
        if (!patientName) {
          return false
        }
        // Split the full name into parts and check if any part matches
        const nameParts = patientName.split(/\s+/)
        const matchesName = nameParts.some(part => part.includes(nameSearchTerm))
        if (!matchesName) {
          return false
        }
      }
      
      // Patient last name filter
      if (filterPatientLastName && filterPatientLastName.trim() !== '') {
        const lastNameSearchTerm = filterPatientLastName.toLowerCase().trim()
        const patientName = (conversation.patientInfo?.name || '').toString().toLowerCase()
        if (!patientName) {
          return false
        }
        // Split the full name into parts and check if any part matches (typically last part is last name)
        const nameParts = patientName.split(/\s+/)
        const matchesLastName = nameParts.some(part => part.includes(lastNameSearchTerm))
        if (!matchesLastName) {
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
  
  const getSituationOrder = (conversation) => {
    const situationConfig = getSituationConfig(conversation.situation, conversation.situationLevel)
    const orderMap = {
      'situation-regular': 0,
      'situation-warning': 1,
      'situation-danger': 2
    }
    return orderMap[situationConfig.class] ?? 99
  }

  const getTimeValue = (value) => {
    if (!value) return 0
    const time = new Date(value).getTime()
    return isNaN(time) ? 0 : time
  }

  const getPatientLabel = (conversation) => (
    (conversation.patientInfo?.name || conversation.patientId || conversation.id || '')
      .toString()
      .toLowerCase()
  )

  const getSortValue = (conversation, key) => {
    switch (key) {
      case 'patient':
        return getPatientLabel(conversation)
      case 'situation':
        return getSituationOrder(conversation)
      case 'createdAt':
        return getTimeValue(conversation.created_at || conversation.createdAt || conversation.session_start)
      case 'updatedAt':
        return getTimeValue(conversation.updated_at || conversation.lastUpdated || conversation.session_end)
      default:
        return null
    }
  }

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
      }
      return { key, direction: 'desc' }
    })
  }

  const sortedConversations = [...displayConversations].sort((a, b) => {
    if (sortConfig.key !== 'default') {
      const valueA = getSortValue(a, sortConfig.key)
      const valueB = getSortValue(b, sortConfig.key)

      if (valueA !== valueB) {
        if (typeof valueA === 'number' && typeof valueB === 'number') {
          const diff = valueB - valueA
          return sortConfig.direction === 'asc' ? -diff : diff
        }

        const comparison = valueA > valueB ? 1 : valueA < valueB ? -1 : 0
        return sortConfig.direction === 'asc' ? comparison : -comparison
      }
    }

    const patientA = (a.patientInfo?.name || a.patientId || a.id || '').toString().toLowerCase()
    const patientB = (b.patientInfo?.name || b.patientId || b.id || '').toString().toLowerCase()

    if (patientA !== patientB) {
      return patientA.localeCompare(patientB)
    }

    const situationOrderA = getSituationOrder(a)
    const situationOrderB = getSituationOrder(b)
    if (situationOrderA !== situationOrderB) {
      return situationOrderA - situationOrderB
    }

    const creationA = getTimeValue(a.created_at || a.createdAt || a.session_start)
    const creationB = getTimeValue(b.created_at || b.createdAt || b.session_start)
    if (creationA !== creationB) {
      return creationB - creationA
    }

    const updatedA = getTimeValue(a.updated_at || a.lastUpdated || a.session_end)
    const updatedB = getTimeValue(b.updated_at || b.lastUpdated || b.session_end)
    return updatedB - updatedA
  })

  // Reset filters
  const resetFilters = () => {
    setFilterSearch('')
    setFilterPatientName('')
    setFilterPatientLastName('')
    setFilterStatus('all')
    setFilterSituation('all')
    setFilterDateFrom('')
    setFilterDateTo('')
    setFilterUpdatedFrom('')
    setFilterUpdatedTo('')
    setCurrentPage(1) // Reset to first page when filters are reset
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
  
  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [filterSearch, filterPatientName, filterPatientLastName, filterStatus, filterSituation, filterDateFrom, filterDateTo, filterUpdatedFrom, filterUpdatedTo])
  
  // Calculate pagination
  const totalPages = Math.ceil(sortedConversations.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedConversations = sortedConversations.slice(startIndex, endIndex)

  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) {
      return '↕'
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓'
  }
  
  // Pagination handlers
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page)
      // Scroll to top of table
      const tableContainer = document.querySelector('.conversation-table-container')
      if (tableContainer) {
        tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }
  
  const goToPreviousPage = () => goToPage(currentPage - 1)
  const goToNextPage = () => goToPage(currentPage + 1)
  
  // Count active filters
  const activeFiltersCount = 
    (filterSearch.trim() !== '' ? 1 : 0) +
    (filterPatientName.trim() !== '' ? 1 : 0) +
    (filterPatientLastName.trim() !== '' ? 1 : 0) +
    (filterStatus !== 'all' ? 1 : 0) +
    (filterSituation !== 'all' ? 1 : 0) +
    (filterDateFrom !== '' ? 1 : 0) +
    (filterDateTo !== '' ? 1 : 0) +
    (filterUpdatedFrom !== '' ? 1 : 0) +
    (filterUpdatedTo !== '' ? 1 : 0)

  const formatDateTime = useCallback((dateString) => {
    const locale = i18n.language?.startsWith('it') ? 'it-IT' : 'en-US'
    const notAvailable = t('conversationList.notAvailable')

    if (!dateString) {
      return {
        date: notAvailable,
        time: notAvailable
      }
    }

    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return {
        date: t('conversationList.date.invalid'),
        time: notAvailable
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
  }, [i18n.language, t])

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

  const handleCancelConversation = async (conversationId) => {
    // Confirm before cancelling
    const confirmed = window.confirm(
      'Sei sicuro di voler annullare questa conversazione?\n\n' +
      'Questa azione segnerà la conversazione come annullata. ' +
      'Questa azione è diversa da "Ferma e segnala" che indica un intervento durante la sessione.'
    )
    
    if (!confirmed) {
      return
    }
    
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversationId}/cancel`, {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (response.data.success) {
        alert('Conversazione annullata con successo')
        if (onConversationsRefresh) {
          onConversationsRefresh()
        }
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

  const handleActionMenu = (conversationId, action) => {
    setOpenDropdownId(null) // Close dropdown after action
    switch (action) {
      case 'stop':
        handleStopAndReport(conversationId)
        break
      case 'complete':
        handleCompleteConversation(conversationId)
        break
      case 'cancel':
        handleCancelConversation(conversationId)
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

    const dateLocale = i18n.language?.startsWith('it') ? Italian : undefined

    const fpOptions = {
      dateFormat: 'd/m/Y',
      locale: dateLocale,
      allowInput: true,
      clickOpens: true
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
  }, [filtersOpen, filterDateFrom, filterDateTo, filterUpdatedFrom, filterUpdatedTo, i18n.language])

  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <h3>{t('conversationList.title')}</h3>
        <div className="conversation-stats">
          <span className="total-conversations">
            {t('conversationList.stats.total', { count: displayConversations.length || 0 })}
          </span>
          <span className="active-conversations">
            {t('conversationList.stats.active', {
              count: displayConversations.filter(c => c && c.status === 'IN_PROGRESS').length || 0
            })}
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
          <span>{t('conversationList.filters.toggle')}</span>
          {activeFiltersCount > 0 && (
            <span className="filter-badge">{activeFiltersCount}</span>
          )}
          <span className={`toggle-arrow ${filtersOpen ? 'open' : ''}`}>▼</span>
        </button>
        
        <div className={`filters-content ${filtersOpen ? 'open' : ''}`}>
            <div className="filters-grid">
              {/* Patient ID - First column */}
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.searchLabel')}</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder={t('conversationList.filters.searchPlaceholder')}
                  value={filterSearch}
                  onChange={(e) => setFilterSearch(e.target.value)}
                />
              </div>
              
              {/* Patient Name - New column */}
              <div className="filter-group" key="patient-name-filter">
                <label className="filter-label">{t('conversationList.filters.patientNameLabel')}</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder={t('conversationList.filters.patientNamePlaceholder')}
                  value={filterPatientName}
                  onChange={(e) => setFilterPatientName(e.target.value)}
                />
              </div>
              
              {/* Patient Last Name - New column */}
              <div className="filter-group" key="patient-lastname-filter">
                <label className="filter-label">{t('conversationList.filters.patientLastNameLabel')}</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder={t('conversationList.filters.patientLastNamePlaceholder')}
                  value={filterPatientLastName}
                  onChange={(e) => setFilterPatientLastName(e.target.value)}
                />
              </div>
              
              {/* Status - Second column */}
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.statusLabel')}</label>
                <CustomSelect
                  className="filter-select"
                  value={filterStatus}
                  onChange={setFilterStatus}
                  placeholder={t('conversationList.filters.status.placeholder')}
                  options={[
                    { value: 'all', label: t('conversationList.filters.status.options.all') },
                    { value: 'IN_PROGRESS', label: t('conversationList.filters.status.options.inProgress'), color: '#f57c00' },
                    { value: 'COMPLETED', label: t('conversationList.filters.status.options.completed'), color: '#2e7d32' },
                    { value: 'STOPPED', label: t('conversationList.filters.status.options.stopped'), color: '#d32f2f' },
                    { value: 'NEW', label: t('conversationList.filters.status.options.new'), color: '#2e7d32' },
                    { value: 'CANCELLED', label: t('conversationList.filters.status.options.cancelled'), color: '#616161' }
                  ]}
                />
              </div>
              
              {/* Situation - Third column */}
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.situationLabel')}</label>
                <CustomSelect
                  className="filter-select"
                  value={filterSituation}
                  onChange={setFilterSituation}
                  placeholder={t('conversationList.filters.situation.placeholder')}
                  options={[
                    { value: 'all', label: t('conversationList.filters.situation.options.all') },
                    { value: 'regular', label: t('conversationList.filters.situation.options.regular'), color: '#4caf50' },
                    { value: 'warning', label: t('conversationList.filters.situation.options.warning'), color: '#ff9800' },
                    { value: 'danger', label: t('conversationList.filters.situation.options.danger'), color: '#f44336' }
                  ]}
                />
              </div>
              
              {/* Creation Date - Fourth column */}
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.dateCreatedFrom')}</label>
                <input
                  type="text"
                  ref={dateFromRef}
                  className="filter-input"
                  placeholder={t('conversationList.filters.datePlaceholder')}
                  data-input
                />
              </div>
              
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.dateCreatedTo')}</label>
                <input
                  type="text"
                  ref={dateToRef}
                  className="filter-input"
                  placeholder={t('conversationList.filters.datePlaceholder')}
                  data-input
                />
              </div>
              
              {/* Last Update - Fifth column */}
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.dateUpdatedFrom')}</label>
                <input
                  type="text"
                  ref={updatedFromRef}
                  className="filter-input"
                  placeholder={t('conversationList.filters.datePlaceholder')}
                  data-input
                />
              </div>
              
              <div className="filter-group">
                <label className="filter-label">{t('conversationList.filters.dateUpdatedTo')}</label>
                <input
                  type="text"
                  ref={updatedToRef}
                  className="filter-input"
                  placeholder={t('conversationList.filters.datePlaceholder')}
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
                  {t('conversationList.filters.reset')}
                </button>
              </div>
            </div>
          </div>
      </div>

      <div className="conversation-table-container">
        {sortedConversations.length === 0 ? (
          <div className="conversation-list-empty">
            <div className="empty-icon"></div>
            <div className="empty-text">{t('conversationList.empty.title')}</div>
            <div className="empty-subtext">
              {activeFiltersCount > 0 
                ? t('conversationList.empty.filtered')
                : t('conversationList.empty.unfiltered')}
            </div>
          </div>
        ) : (
          <table className="conversation-table">
            <thead>
              <tr>
                <th>{t('conversationList.table.patient')}</th>
                <th>{t('conversationList.table.status')}</th>
                <th>
                  <button
                    type="button"
                    className="table-sort-button"
                    onClick={() => handleSort('situation')}
                  >
                    {t('conversationList.table.situation')} <span className="sort-indicator">{getSortIndicator('situation')}</span>
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="table-sort-button"
                    onClick={() => handleSort('createdAt')}
                  >
                    {t('conversationList.table.createdAt')} <span className="sort-indicator">{getSortIndicator('createdAt')}</span>
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="table-sort-button"
                    onClick={() => handleSort('updatedAt')}
                  >
                    {t('conversationList.table.updatedAt')} <span className="sort-indicator">{getSortIndicator('updatedAt')}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedConversations.map((conversation) => {
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
              const patientIdentifier = conversation.patientId ?? conversation.id
              const patientName = t('conversationList.patientLabel', { id: patientIdentifier })
              const ageValue = typeof conversation.patientInfo?.age === 'number'
                ? conversation.patientInfo?.age
                : null
              const ageLabel = ageValue !== null
                ? t('conversationList.patientAge', { count: ageValue })
                : t('conversationList.notAvailable')
              const genderLabel = conversation.patientInfo?.gender && conversation.patientInfo.gender !== 'U' && conversation.patientInfo.gender !== null
                ? getGenderLabel(conversation.patientInfo.gender)
                : t('conversationList.gender.unknown')
              const patientMeta = t('conversationList.patientMeta', {
                age: ageLabel,
                gender: genderLabel
              })

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
                        <div className="patient-name">{patientName}</div>
                        <div className="patient-meta">
                          {patientMeta}
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
        
        {/* Pagination Controls */}
        {sortedConversations.length > itemsPerPage && (
          <div className="conversation-pagination">
            <div className="pagination-info">
              <span>
                {t('conversationList.pagination.showing', {
                  start: startIndex + 1,
                  end: Math.min(endIndex, sortedConversations.length),
                  total: sortedConversations.length
                })}
              </span>
            </div>
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                onClick={goToPreviousPage}
                disabled={currentPage === 1}
                aria-label={t('conversationList.pagination.prev')}
              >
                ‹
              </button>
              
              <div className="pagination-numbers">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                  // Show first page, last page, current page, and pages around current
                  if (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  ) {
                    return (
                      <button
                        key={page}
                        className={`pagination-number ${currentPage === page ? 'active' : ''}`}
                        onClick={() => goToPage(page)}
                        aria-label={t('conversationList.pagination.goto', { page })}
                      >
                        {page}
                      </button>
                    )
                  } else if (page === currentPage - 2 || page === currentPage + 2) {
                    return <span key={page} className="pagination-ellipsis">...</span>
                  }
                  return null
                })}
              </div>
              
              <button
                className="pagination-btn"
                onClick={goToNextPage}
                disabled={currentPage === totalPages}
                aria-label={t('conversationList.pagination.next')}
              >
                ›
              </button>
            </div>
          </div>
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
