import { Component } from 'react';
import logger from '../services/logger.js';

/**
 * React Error Boundary
 * 
 * Catches errors in component tree, displays fallback UI,
 * and logs errors to the logging service.
 * 
 * Usage:
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so next render shows fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to logging service
    logger.componentError(error, errorInfo);

    // Store error details for display
    this.setState({
      error,
      errorInfo,
    });

    // Also log to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo } = this.state;
      const isDev = import.meta.env.DEV;

      return (
        <div style={{
          padding: '40px',
          maxWidth: '800px',
          margin: '0 auto',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}>
          <div style={{
            background: '#fee',
            border: '2px solid #c33',
            borderRadius: '8px',
            padding: '24px',
          }}>
            <h1 style={{
              margin: '0 0 16px 0',
              fontSize: '24px',
              color: '#c33',
            }}>
              ⚠️ Something went wrong
            </h1>

            <p style={{
              margin: '0 0 20px 0',
              fontSize: '16px',
              color: '#333',
            }}>
              The application encountered an unexpected error. This has been logged and we'll look into it.
            </p>

            <div style={{
              display: 'flex',
              gap: '12px',
              marginBottom: '24px',
            }}>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '10px 20px',
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                }}
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                style={{
                  padding: '10px 20px',
                  background: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                }}
              >
                Reload Page
              </button>
            </div>

            {isDev && error && (
              <details style={{
                marginTop: '20px',
                padding: '16px',
                background: '#fff',
                border: '1px solid #ddd',
                borderRadius: '4px',
              }}>
                <summary style={{
                  cursor: 'pointer',
                  fontWeight: '600',
                  marginBottom: '12px',
                  color: '#666',
                }}>
                  Error Details (Development Only)
                </summary>

                <div style={{
                  fontSize: '14px',
                  fontFamily: 'monospace',
                }}>
                  <div style={{ marginBottom: '16px' }}>
                    <strong style={{ color: '#c33' }}>{error.name}:</strong>{' '}
                    <span style={{ color: '#333' }}>{error.message}</span>
                  </div>

                  {error.stack && (
                    <div style={{ marginBottom: '16px' }}>
                      <strong>Stack Trace:</strong>
                      <pre style={{
                        margin: '8px 0 0 0',
                        padding: '12px',
                        background: '#f5f5f5',
                        borderRadius: '4px',
                        overflow: 'auto',
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all',
                      }}>
                        {error.stack}
                      </pre>
                    </div>
                  )}

                  {errorInfo && errorInfo.componentStack && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre style={{
                        margin: '8px 0 0 0',
                        padding: '12px',
                        background: '#f5f5f5',
                        borderRadius: '4px',
                        overflow: 'auto',
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all',
                      }}>
                        {errorInfo.componentStack}
                      </pre>
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
