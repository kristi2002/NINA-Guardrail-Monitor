/**
 * Loading Skeleton Component for better loading states
 */

import React, { memo } from 'react';
import './LoadingSkeleton.css';

const LoadingSkeleton = memo(({ 
  type = 'text',
  width,
  height,
  count = 1,
  className = '',
  ...props 
}) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return (
          <div 
            className={`skeleton skeleton-text ${className}`}
            style={{ width, height: height || '1rem' }}
            {...props}
          />
        );
      
      case 'title':
        return (
          <div 
            className={`skeleton skeleton-title ${className}`}
            style={{ width, height: height || '1.5rem' }}
            {...props}
          />
        );
      
      case 'paragraph':
        return (
          <div className={`skeleton-paragraph ${className}`} {...props}>
            <div className="skeleton skeleton-text" style={{ width: '100%', height: '1rem' }} />
            <div className="skeleton skeleton-text" style={{ width: '90%', height: '1rem' }} />
            <div className="skeleton skeleton-text" style={{ width: '75%', height: '1rem' }} />
          </div>
        );
      
      case 'card':
        return (
          <div className={`skeleton-card ${className}`} {...props}>
            <div className="skeleton skeleton-title" style={{ width: '70%', height: '1.5rem' }} />
            <div className="skeleton skeleton-text" style={{ width: '100%', height: '1rem', marginTop: '0.5rem' }} />
            <div className="skeleton skeleton-text" style={{ width: '85%', height: '1rem', marginTop: '0.25rem' }} />
            <div className="skeleton skeleton-text" style={{ width: '60%', height: '1rem', marginTop: '0.25rem' }} />
            <div className="skeleton skeleton-button" style={{ width: '100px', height: '2rem', marginTop: '1rem' }} />
          </div>
        );
      
      case 'table':
        return (
          <div className={`skeleton-table ${className}`} {...props}>
            <div className="skeleton-table-header">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="skeleton skeleton-text" style={{ width: '100%', height: '1rem' }} />
              ))}
            </div>
            <div className="skeleton-table-body">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="skeleton-table-row">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="skeleton skeleton-text" style={{ width: '100%', height: '1rem' }} />
                  ))}
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'list':
        return (
          <div className={`skeleton-list ${className}`} {...props}>
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="skeleton-list-item">
                <div className="skeleton skeleton-avatar" style={{ width: '2rem', height: '2rem' }} />
                <div className="skeleton-list-content">
                  <div className="skeleton skeleton-text" style={{ width: '60%', height: '1rem' }} />
                  <div className="skeleton skeleton-text" style={{ width: '40%', height: '0.875rem', marginTop: '0.25rem' }} />
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'avatar':
        return (
          <div 
            className={`skeleton skeleton-avatar ${className}`}
            style={{ width: width || '2rem', height: height || '2rem' }}
            {...props}
          />
        );
      
      case 'button':
        return (
          <div 
            className={`skeleton skeleton-button ${className}`}
            style={{ width, height: height || '2rem' }}
            {...props}
          />
        );
      
      case 'image':
        return (
          <div 
            className={`skeleton skeleton-image ${className}`}
            style={{ width, height: height || '200px' }}
            {...props}
          />
        );
      
      case 'chart':
        return (
          <div className={`skeleton-chart ${className}`} {...props}>
            <div className="skeleton-chart-header">
              <div className="skeleton skeleton-title" style={{ width: '40%', height: '1.5rem' }} />
              <div className="skeleton skeleton-text" style={{ width: '20%', height: '1rem' }} />
            </div>
            <div className="skeleton-chart-content">
              <div className="skeleton skeleton-image" style={{ width: '100%', height: '200px' }} />
            </div>
          </div>
        );
      
      default:
        return (
          <div 
            className={`skeleton skeleton-default ${className}`}
            style={{ width, height }}
            {...props}
          />
        );
    }
  };

  if (count > 1) {
    return (
      <div className="skeleton-container">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i}>
            {renderSkeleton()}
          </div>
        ))}
      </div>
    );
  }

  return renderSkeleton();
});

LoadingSkeleton.displayName = 'LoadingSkeleton';

export default LoadingSkeleton;

