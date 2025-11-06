import { useState, useMemo } from 'react'
import { ConversationList, ConversationListSkeleton, ConversationStatus, ConversationStatusSkeleton } from '../components/conversations'
import { Sidebar } from '../components/common'
import { DashboardHeader, DashboardMetrics } from './dashboard/components'
import { useDashboardData } from './dashboard/hooks'
import './dashboard/Dashboard.css'

function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const {
    metrics,
    error,
    alerts,
    conversations,
    lastUpdated,
    previousMetrics,
    fetchAlerts,
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
        alerts={alerts}
        lastUpdated={lastUpdated}
        onOpenSidebar={() => setSidebarOpen(true)}
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

      <Sidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        alerts={alerts}
        onAlertsRefresh={fetchAlerts}
      />
    </div>
  )
}

export default Dashboard

