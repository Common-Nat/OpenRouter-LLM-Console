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

// Environment-based log level filtering
const LOG_CONFIG = {
  development: {
    console: ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
    backend: ['ERROR', 'CRITICAL'], // Only errors to backend in dev
  },
  production: {
    console: ['ERROR', 'CRITICAL'], // Minimal console noise
    backend: ['INFO', 'WARN', 'ERROR', 'CRITICAL'], // Full backend logging
  },
};

const BACKEND_ENDPOINT = '/api/logs';
const BATCH_INTERVAL = 5000; // Send logs every 5s in batches
const MAX_BATCH_SIZE = 50;
const MAX_QUEUE_SIZE = 500; // Prevent memory bloat
const MAX_OFFLINE_LOGS = 100; // localStorage limit
const MAX_RETRY_ATTEMPTS = 5;

class Logger {
  constructor() {
    this.isDev = import.meta.env.DEV;
    this.env = import.meta.env.MODE || (this.isDev ? 'development' : 'production');
    this.config = LOG_CONFIG[this.env] || LOG_CONFIG.development;
    this.sessionId = this.generateSessionId();
    this.logQueue = [];
    this.failedQueue = []; // Logs that failed to send
    this.batchTimer = null;
    this.retryTimer = null;
    this.retryCount = 0;
    
    // Restore any persisted logs from previous session
    this.restoreFromStorage();
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
    if (data === null || data === undefined) return data;
    if (typeof data !== 'object') return data;
    
    const sensitive = ['password', 'token', 'api_key', 'apikey', 'secret'];
    const sanitized = JSON.parse(JSON.stringify(data));
    
    const redact = (obj) => {
      if (typeof obj !== 'object' || obj === null) return;
      
      for (const key in obj) {
        const lowerKey = key.toLowerCase();
        if (sensitive.some(s => lowerKey.includes(s))) {
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

    // Log to console based on environment config
    if (this.shouldLogToConsole(level)) {
      const consoleMethod = level === LOG_LEVELS.ERROR || level === LOG_LEVELS.CRITICAL 
        ? 'error' 
        : level === LOG_LEVELS.WARN 
        ? 'warn' 
        : 'log';
      
      console[consoleMethod](`[${level.toUpperCase()}]`, message, meta);
    }

    // Queue for backend based on environment config
    if (this.shouldLogToBackend(level)) {
      this.queueForBackend(logEntry);
    }
  }

  /**
   * Queue log for batch sending to backend
   */
  queueForBackend(logEntry) {
    this.logQueue.push(logEntry);

    // Prevent memory bloat with circular buffer
    if (this.logQueue.length > MAX_QUEUE_SIZE) {
      this.logQueue = this.logQueue.slice(-MAX_QUEUE_SIZE);
    }

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
   * Send queued logs to backend with exponential backoff retry
   */
  async flushLogs() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    // Try to send any previously failed logs first
    if (this.failedQueue.length > 0) {
      const failedLogs = [...this.failedQueue];
      this.failedQueue = [];
      this.logQueue.unshift(...failedLogs);
    }

    if (this.logQueue.length === 0) return;

    const logsToSend = [...this.logQueue];
    this.logQueue = [];

    try {
      const response = await fetch(BACKEND_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
      });

      if (response.ok) {
        // Success - reset retry counter
        this.retryCount = 0;
        // Clear any persisted offline logs
        localStorage.removeItem('logger_offline_queue');
      } else if (response.status === 429) {
        // Rate limited - respect Retry-After header
        const retryAfter = response.headers.get('Retry-After');
        const delayMs = retryAfter ? parseInt(retryAfter) * 1000 : 5000;
        this.scheduleRetry(logsToSend, delayMs);
      } else if (response.status >= 500) {
        // Server error - retry with backoff
        this.scheduleRetry(logsToSend);
      } else {
        // Client error (4xx) - don't retry, log failed
        if (this.isDev) {
          console.warn('Logs rejected by backend:', response.status);
        }
      }
    } catch (err) {
      // Network error - retry with exponential backoff
      if (this.isDev) {
        console.warn('Failed to send logs to backend:', err.message);
      }
      this.scheduleRetry(logsToSend);
    }
  }

  /**
   * Schedule retry with exponential backoff
   */
  scheduleRetry(logsToSend, customDelay = null) {
    if (this.retryCount >= MAX_RETRY_ATTEMPTS) {
      // Give up after max retries - persist to localStorage
      this.failedQueue.push(...logsToSend);
      this.persistToStorage();
      this.retryCount = 0;
      return;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 30s)
    const backoffMs = customDelay || Math.min(1000 * Math.pow(2, this.retryCount), 30000);
    this.retryCount++;

    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }

    this.retryTimer = setTimeout(() => {
      this.logQueue.unshift(...logsToSend);
      this.flushLogs();
    }, backoffMs);
  }

  /**
   * Check if log level should be sent to console
   */
  shouldLogToConsole(level) {
    return this.config.console.includes(level.toUpperCase());
  }

  /**
   * Check if log level should be sent to backend
   */
  shouldLogToBackend(level) {
    return this.config.backend.includes(level.toUpperCase());
  }

  /**
   * Persist failed logs to localStorage
   */
  persistToStorage() {
    if (this.failedQueue.length === 0) return;

    try {
      // Keep only last N logs to respect storage limits
      const logsToStore = this.failedQueue.slice(-MAX_OFFLINE_LOGS);
      localStorage.setItem('logger_offline_queue', JSON.stringify(logsToStore));
    } catch (err) {
      // localStorage might be disabled or quota exceeded
      if (this.isDev) {
        console.warn('Failed to persist logs to localStorage:', err.message);
      }
    }
  }

  /**
   * Restore persisted logs from localStorage
   */
  restoreFromStorage() {
    try {
      const stored = localStorage.getItem('logger_offline_queue');
      if (stored) {
        this.failedQueue = JSON.parse(stored);
        // Try to send restored logs after a brief delay
        setTimeout(() => {
          if (this.failedQueue.length > 0) {
            this.flushLogs();
          }
        }, 2000);
      }
    } catch (err) {
      // Invalid JSON or localStorage disabled
      if (this.isDev) {
        console.warn('Failed to restore logs from localStorage:', err.message);
      }
    }
  }

  /**
   * Synchronous flush using sendBeacon for guaranteed delivery
   * Use this for page unload scenarios
   */
  flushSync() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    // Combine current queue with failed queue
    const allLogs = [...this.failedQueue, ...this.logQueue];
    if (allLogs.length === 0) return;

    this.logQueue = [];
    this.failedQueue = [];

    try {
      // sendBeacon guarantees delivery even during page unload
      const blob = new Blob(
        [JSON.stringify({ logs: allLogs })],
        { type: 'application/json' }
      );
      navigator.sendBeacon(BACKEND_ENDPOINT, blob);
    } catch (err) {
      // Fallback to localStorage if sendBeacon fails
      this.failedQueue = allLogs;
      this.persistToStorage();
    }
  }

  // Convenience methods
  debug(message, meta = {}) {
    this.log(LOG_LEVELS.DEBUG, message, meta);
  }

  info(message, meta = {}) {
    this.log(LOG_LEVELS.INFO, message, meta);
  }

  warn(message, meta = {}) {
    this.log(LOG_LEVELS.WARN, message, meta);
  }

  error(message, meta = {}) {
    this.log(LOG_LEVELS.ERROR, message, meta);
  }

  critical(message, meta = {}) {
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
  componentError(error, errorInfo = {}) {
    this.error('React Component Error', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      ...errorInfo,
    });
  }
}

// Singleton instance
const logger = new Logger();

// Flush logs before page unload using sendBeacon for guaranteed delivery
window.addEventListener('beforeunload', () => {
  logger.flushSync();
});

// Also flush on visibility change (tab switch, minimize)
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    logger.flushSync();
  }
});

export default logger;
export { LOG_LEVELS };
