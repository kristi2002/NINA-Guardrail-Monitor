import { useState, useEffect } from 'react'
import axios from 'axios'
import ConversationDetailModal from './ConversationDetailModal'
import './ConversationList.css'

function ConversationList({ conversations = [], onConversationsRefresh }) {
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [loading, setLoading] = useState(false)

  // Use conversations from props (from API)
  const displayConversations = conversations || []

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
    return configs[situation] || configs['Regolare']
  }

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
    try {
      setLoading(true)
      const response = await axios.post(`/api/conversations/${conversationId}/stop`)
      
      if (response.data.success) {
        alert('Conversazione fermata e segnalata con successo')
        if (onConversationsRefresh) {
          onConversationsRefresh()
        }
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

  const handleActionMenu = (conversationId, action) => {
    switch (action) {
      case 'details':
        const conversation = displayConversations.find(c => c.id === conversationId)
        if (conversation) {
          handleConversationClick(conversation)
        }
        break
      case 'stop':
        handleStopAndReport(conversationId)
        break
      default:
        console.log('Unknown action:', action)
    }
  }

  if (displayConversations.length === 0) {
    return (
      <div className="conversation-list-empty">
        <div className="empty-icon">💬</div>
        <div className="empty-text">Nessuna conversazione attiva</div>
        <div className="empty-subtext">Il sistema è in attesa di nuove conversazioni</div>
      </div>
    )
  }

  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <h3>Monitoraggio conversazioni</h3>
        <div className="conversation-stats">
          <span className="total-conversations">{displayConversations.length} conversazioni</span>
          <span className="active-conversations">
            {displayConversations.filter(c => c.status === 'IN_PROGRESS').length} attive
          </span>
        </div>
      </div>

      <div className="conversation-table-container">
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
              const statusConfig = getStatusConfig(conversation.status)
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
                  className={`conversation-row ${conversation.situationLevel === 'high' ? 'high-risk' : ''}`}
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
                          {conversation.patientInfo?.name || `Paziente ${conversation.patientId}`}
                        </div>
                        <div className="patient-meta">
                          {conversation.patientInfo?.age || 'N/A'} anni, {conversation.patientInfo?.gender || 'N/A'}
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
                      style={{ backgroundColor: situationConfig.color }}
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
                        onClick={(e) => {
                          e.stopPropagation()
                          // Simple action for now - open details
                          handleActionMenu(conversation.id, 'details')
                        }}
                      >
                        <span className="action-icon">▼</span>
                        Azioni
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
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
