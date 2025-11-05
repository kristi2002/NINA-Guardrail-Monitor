import LoadingSkeleton from './LoadingSkeleton'
import './MetricCard.css'

function MetricCardSkeleton() {
  return (
    <div className="metric-card">
      <div className="card-background"></div>
      <div className="card-content">
        <div className="metric-header">
          <div className="header-left">
            <div className="icon-container">
              <LoadingSkeleton type="avatar" width="2rem" height="2rem" />
            </div>
            <LoadingSkeleton type="text" width="60%" height="1rem" />
          </div>
        </div>
        
        <div className="metric-value-container">
          <LoadingSkeleton type="text" width="40%" height="2rem" />
        </div>
      </div>
    </div>
  )
}

export default MetricCardSkeleton
