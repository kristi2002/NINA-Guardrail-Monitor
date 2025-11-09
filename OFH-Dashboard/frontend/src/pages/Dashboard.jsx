import { useMemo } from 'react'
import { ConversationList, ConversationListSkeleton, ConversationStatus, ConversationStatusSkeleton } from '../components/conversations'
import { DashboardHeader, DashboardMetrics } from './dashboard/components'
import { useDashboardData } from './dashboard/hooks'
import './dashboard/Dashboard.css'

function Dashboard() {
  const {
    metrics,
    error,
    conversations,
    lastUpdated,
    previousMetrics,
    fetchConversations
  } = useDashboardData()

  // Memoize expensive calculations
  const activeConversations = useMemo(() => {
    return conversations.filter(c => c.status === 'IN_PROGRESS').length
  }, [conversations])

  const criticalAlerts = useMemo(() => {
    return conversations.filter(c => c.situationLevel === 'high' || c.situationLevel === 'critical').length
  }, [conversations])

  if (error && !metrics && conversations.length === 0) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="dashboard">
      <DashboardHeader 
        lastUpdated={lastUpdated}
      />
      
      {!metrics ? (
        <ConversationStatusSkeleton />
      ) : (
        <ConversationStatus conversations={conversations} />
      )}

      {!metrics && conversations.length === 0 ? (
        <ConversationListSkeleton />
      ) : (
        <ConversationList 
          conversations={conversations}
          onConversationsRefresh={fetchConversations}
        />
      )}

      <DashboardMetrics 
        metrics={metrics}
        previousMetrics={previousMetrics}
      />
    </div>
  )
}

export default Dashboard

