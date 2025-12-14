/**
 * Centralized Frontend Logging Service
 * 
 * Features:
 * - Structured logging with severity levels
 * - Environment-aware (console in dev, backend in prod)
 * - Context enrichment (session, route, timestamp)
 * - Privacy-safe (filters sensitive data)
 * - Debounced backend calls to prevent spam
 */

const LOG_LEVELS = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
  CRITICAL: 'critical',
};

const BACKEND_ENDPOINT = '/api/logs';
const BATCH_INTERVAL = 5000; // Send logs every 5s in batches
const MAX_BATCH_SIZE = 50;

class Logger {
  constructor() {
    this.isDev = import.meta.env.DEV;
    this.sessionId = this.generateSessionId();
    this.logQueue = [];
    this.batchTimer = null;
  }

  generateSessionId() {
    // Generate unique session ID for tracking user session
    const stored = sessionStorage.getItem('logger_session_id');
    if (stored) return stored;
    
    const id = `fe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('logger_session_id', id);
    return id;
  }

  /**
   * Get current context for log enrichment
   */
  getContext() {
    return {
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      route: window.location.pathname,
      userAgent: navigator.userAgent,
    };
  }

  /**
   * Sanitize data to remove sensitive information
   */
  sanitize(data) {
    if (!data) return data;
    
    const sensitive = ['password', 'token', 'api_key', 'apiKey', 'secret'];
    const sanitized = JSON.parse(JSON.stringify(data));
    
    const redact = (obj) => {
      if (typeof obj !== 'object' || obj === null) return;
      
      for (const key in obj) {
        if (sensitive.some(s => key.toLowerCase().includes(s))) {
          obj[key] = '[REDACTED]';
        } else if (typeof obj[key] === 'object') {
          redact(obj[key]);
        }
      }
    };
    
    redact(sanitized);
    return sanitized;
  }

  /**
   * Core logging method
   */
  log(level, message, meta = {}) {
    const logEntry = {
      level,
      message,
      meta: this.sanitize(meta),
      context: this.getContext(),
    };

    // Always log to console in development
    if (this.isDev) {
      const consoleMethod = level === LOG_LEVELS.ERROR || level === LOG_LEVELS.CRITICAL 
        ? 'error' 
        : level === LOG_LEVELS.WARN 
        ? 'warn' 
        : 'log';
      
      console[consoleMethod](`[${level.toUpperCase()}]`, message, meta);
    }

    // Queue for backend in production or for ERROR/CRITICAL in dev
    if (!this.isDev || level === LOG_LEVELS.ERROR || level === LOG_LEVELS.CRITICAL) {
      this.queueForBackend(logEntry);
    }
  }

  /**
   * Queue log for batch sending to backend
   */
  queueForBackend(logEntry) {
    this.logQueue.push(logEntry);

    // Send immediately for critical errors
    if (logEntry.level === LOG_LEVELS.CRITICAL) {
      this.flushLogs();
      return;
    }

    // Send immediately if queue is full
    if (this.logQueue.length >= MAX_BATCH_SIZE) {
      this.flushLogs();
      return;
    }

    // Schedule batch send
    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        this.flushLogs();
      }, BATCH_INTERVAL);
    }
  }

  /**
   * Send queued logs to backend
   */
  async flushLogs() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    if (this.logQueue.length === 0) return;

    const logsToSend = [...this.logQueue];
    this.logQueue = [];

    try {
      await fetch(BACKEND_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch (err) {
      // Fail silently to avoid infinite error loops
      // Only log to console if in dev
      if (this.isDev) {
        console.warn('Failed to send logs to backend:', err);
      }
    }
  }

  // Convenience methods
  debug(message, meta) {
    this.log(LOG_LEVELS.DEBUG, message, meta);
  }

  info(message, meta) {
    this.log(LOG_LEVELS.INFO, message, meta);
  }

  warn(message, meta) {
    this.log(LOG_LEVELS.WARN, message, meta);
  }

  error(message, meta) {
    this.log(LOG_LEVELS.ERROR, message, meta);
  }

  critical(message, meta) {
    this.log(LOG_LEVELS.CRITICAL, message, meta);
  }

  /**
   * Log API error with structured format
   */
  apiError(error, endpoint, method = 'GET') {
    this.error('API Request Failed', {
      endpoint,
      method,
      status: error.status,
      code: error.code,
      message: error.message,
      resourceType: error.resourceType,
      resourceId: error.resourceId,
      details: error.details,
    });
  }

  /**
   * Log React component error
   */
  componentError(error, errorInfo) {
    this.error('React Component Error', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      componentStack: errorInfo.componentStack,
    });
  }
}

// Singleton instance
const logger = new Logger();

// Flush logs before page unload
window.addEventListener('beforeunload', () => {
  logger.flushLogs();
});

export default logger;
export { LOG_LEVELS };
