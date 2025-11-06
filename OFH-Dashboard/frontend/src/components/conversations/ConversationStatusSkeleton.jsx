import { LoadingSkeleton } from '../ui'
import './ConversationStatus.css'

function ConversationStatusSkeleton() {
  return (
    <div className="conversation-status">
      <div className="status-header">
        <LoadingSkeleton type="text" width="200px" height="1.5rem" />
      </div>
      <div className="status-cards">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="status-card">
            <LoadingSkeleton type="text" width="80px" height="1rem" />
            <LoadingSkeleton type="text" width="60px" height="2rem" style={{ marginTop: '0.5rem' }} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default ConversationStatusSkeleton
