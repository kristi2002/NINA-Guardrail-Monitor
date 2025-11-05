import LoadingSkeleton from './LoadingSkeleton'
import './ConversationList.css'

function ConversationListSkeleton() {
  return (
    <div className="conversation-list-container">
      <div className="filters-section">
        <LoadingSkeleton type="text" width="150px" height="1.5rem" style={{ marginBottom: '1rem' }} />
      </div>
      <LoadingSkeleton type="table" />
    </div>
  )
}

export default ConversationListSkeleton
