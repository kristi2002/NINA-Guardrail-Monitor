/**
 * Error Boundary Component for catching and handling React errors
 */

import React, { Component } from 'react';
import './ErrorBoundary.css';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState({
      error,
      errorInfo
    });

    // Log to error reporting service (if available)
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: error.toString(),
        fatal: false,
        error_id: this.state.errorId
      });
    }

    // Send to custom error reporting service
    this.reportError(error, errorInfo);
  }

  reportError = (error, errorInfo) => {
    // This would typically send to an error reporting service like Sentry
    // For now, we'll just log it
    const errorReport = {
      errorId: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    console.log('Error Report:', errorReport);
    
    // In a real application, you would send this to your error reporting service
    // Example: Sentry.captureException(error, { extra: errorReport });
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleReportBug = () => {
    const errorReport = {
      errorId: this.state.errorId,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      componentStack: this.state.errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Create a mailto link with error details
    const subject = `Error Report - ${this.state.errorId}`;
    const body = `Error Details:\n\n${JSON.stringify(errorReport, null, 2)}`;
    const mailtoLink = `mailto:support@example.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    window.open(mailtoLink);
  };

  render() {
    if (this.state.hasError) {
      const { fallback, showDetails = false } = this.props;
      
      if (fallback) {
        return fallback(this.state.error, this.handleRetry);
      }

      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">
              ⚠️
            </div>
            
            <h2 className="error-title">
              Something went wrong
            </h2>
            
            <p className="error-message">
              We're sorry, but something unexpected happened. Our team has been notified.
            </p>
            
            <div className="error-actions">
              <button 
                className="btn-retry"
                onClick={this.handleRetry}
              >
                Try Again
              </button>
              
              <button 
                className="btn-reload"
                onClick={this.handleReload}
              >
                Reload Page
              </button>
              
              <button 
                className="btn-report"
                onClick={this.handleReportBug}
              >
                Report Bug
              </button>
            </div>

            {showDetails && this.state.error && (
              <details className="error-details">
                <summary>Error Details</summary>
                <div className="error-details-content">
                  <div className="error-id">
                    <strong>Error ID:</strong> {this.state.errorId}
                  </div>
                  
                  <div className="error-message-detail">
                    <strong>Message:</strong> {this.state.error.message}
                  </div>
                  
                  <div className="error-stack">
                    <strong>Stack Trace:</strong>
                    <pre>{this.state.error.stack}</pre>
                  </div>
                  
                  {this.state.errorInfo && (
                    <div className="error-component-stack">
                      <strong>Component Stack:</strong>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;