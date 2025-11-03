/**
 * Network Error Component for handling API and network errors
 */

import React, { memo, useCallback, useState } from 'react';
import { useAuth } from '../contexts';
import './NetworkError.css';

const NetworkError = memo(({ 
  error, 
  onRetry, 
  onDismiss,
  showDetails = false,
  className = '' 
}) => {
  const { user } = useAuth();
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = useCallback(async () => {
    if (isRetrying) return;
    
    setIsRetrying(true);
    try {
      await onRetry?.();
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, isRetrying]);

  const handleDismiss = useCallback(() => {
    onDismiss?.();
  }, [onDismiss]);

  const getErrorType = useCallback(() => {
    if (!error) return 'Unknown';
    
    if (error.code === 'NETWORK_ERROR') return 'Network Error';
    if (error.code === 'TIMEOUT') return 'Timeout';
    if (error.code === 'SERVER_ERROR') return 'Server Error';
    if (error.code === 'UNAUTHORIZED') return 'Unauthorized';
    if (error.code === 'FORBIDDEN') return 'Forbidden';
    if (error.code === 'NOT_FOUND') return 'Not Found';
    if (error.code === 'VALIDATION_ERROR') return 'Validation Error';
    
    return 'Network Error';
  }, [error]);

  const getErrorMessage = useCallback(() => {
    if (!error) return 'An unknown error occurred';
    
    if (error.message) return error.message;
    if (error.response?.data?.message) return error.response.data.message;
    if (error.response?.statusText) return error.response.statusText;
    
    return 'An error occurred while processing your request';
  }, [error]);

  const getErrorIcon = useCallback(() => {
    const errorType = getErrorType();
    
    switch (errorType) {
      case 'Network Error':
        return '🌐';
      case 'Timeout':
        return '⏱️';
      case 'Server Error':
        return '🔧';
      case 'Unauthorized':
        return '🔒';
      case 'Forbidden':
        return '🚫';
      case 'Not Found':
        return '🔍';
      case 'Validation Error':
        return '⚠️';
      default:
        return '❌';
    }
  }, [getErrorType]);

  const getErrorColor = useCallback(() => {
    const errorType = getErrorType();
    
    switch (errorType) {
      case 'Network Error':
      case 'Timeout':
        return '#f59e0b';
      case 'Server Error':
        return '#ef4444';
      case 'Unauthorized':
      case 'Forbidden':
        return '#dc2626';
      case 'Not Found':
        return '#6b7280';
      case 'Validation Error':
        return '#f59e0b';
      default:
        return '#ef4444';
    }
  }, [getErrorType]);

  if (!error) return null;

  const errorType = getErrorType();
  const errorMessage = getErrorMessage();
  const errorIcon = getErrorIcon();
  const errorColor = getErrorColor();

  return (
    <div className={`network-error ${className}`} style={{ borderColor: errorColor }}>
      <div className="network-error-content">
        <div className="network-error-header">
          <div className="network-error-icon">
            {errorIcon}
          </div>
          <div className="network-error-info">
            <h3 className="network-error-title">
              {errorType}
            </h3>
            <p className="network-error-message">
              {errorMessage}
            </p>
          </div>
          <button 
            className="network-error-dismiss"
            onClick={handleDismiss}
            title="Dismiss error"
          >
            ✕
          </button>
        </div>

        {showDetails && (
          <div className="network-error-details">
            <div className="network-error-detail-item">
              <strong>Status Code:</strong> {error.response?.status || 'N/A'}
            </div>
            <div className="network-error-detail-item">
              <strong>Request URL:</strong> {error.config?.url || 'N/A'}
            </div>
            <div className="network-error-detail-item">
              <strong>Request Method:</strong> {error.config?.method?.toUpperCase() || 'N/A'}
            </div>
            {error.response?.data && (
              <div className="network-error-detail-item">
                <strong>Response Data:</strong>
                <pre className="network-error-response">
                  {JSON.stringify(error.response.data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        <div className="network-error-actions">
          <button 
            className="btn-retry"
            onClick={handleRetry}
            disabled={isRetrying}
          >
            {isRetrying ? 'Retrying...' : 'Retry'}
          </button>
          
          {errorType === 'Unauthorized' && (
            <button 
              className="btn-login"
              onClick={() => window.location.href = '/login'}
            >
              Login
            </button>
          )}
        </div>
      </div>
    </div>
  );
});

NetworkError.displayName = 'NetworkError';

export default NetworkError;

