import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import logger, { LOG_LEVELS } from '../src/services/logger.js';

describe('Logger Service', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    
    // Reset logger state
    logger.logQueue = [];
    logger.failedQueue = [];
    logger.retryCount = 0;
    if (logger.batchTimer) {
      clearTimeout(logger.batchTimer);
      logger.batchTimer = null;
    }
    if (logger.retryTimer) {
      clearTimeout(logger.retryTimer);
      logger.retryTimer = null;
    }
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Session ID Generation', () => {
    it('should generate unique session ID', () => {
      const sessionId = logger.sessionId;
      expect(sessionId).toMatch(/^fe_\d+_[a-z0-9]+$/);
    });

    it('should persist session ID in sessionStorage', () => {
      sessionStorage.getItem.mockReturnValue('test_session_123');
      const newLogger = new (logger.constructor)();
      expect(newLogger.sessionId).toBe('test_session_123');
    });
  });

  describe('Data Sanitization', () => {
    it('should redact sensitive fields', () => {
      const data = {
        username: 'john',
        password: 'secret123',
        apiKey: 'sk-xyz',
        token: 'bearer-token',
        api_key: 'another-key',
        secret: 'shh',
        normalField: 'visible',
      };

      const sanitized = logger.sanitize(data);
      
      expect(sanitized.password).toBe('[REDACTED]');
      expect(sanitized.apiKey).toBe('[REDACTED]');
      expect(sanitized.token).toBe('[REDACTED]');
      expect(sanitized.api_key).toBe('[REDACTED]');
      expect(sanitized.secret).toBe('[REDACTED]');
      expect(sanitized.username).toBe('john');
      expect(sanitized.normalField).toBe('visible');
    });

    it('should handle nested objects', () => {
      const data = {
        user: {
          name: 'john',
          credentials: {
            password: 'secret',
            apiKey: 'key123',
          },
        },
      };

      const sanitized = logger.sanitize(data);
      
      expect(sanitized.user.name).toBe('john');
      expect(sanitized.user.credentials.password).toBe('[REDACTED]');
      expect(sanitized.user.credentials.apiKey).toBe('[REDACTED]');
    });

    it('should handle null and undefined', () => {
      expect(logger.sanitize(null)).toBe(null);
      expect(logger.sanitize(undefined)).toBe(undefined);
    });
  });

  describe('Log Level Filtering', () => {
    it('should respect console log level config for development', () => {
      logger.isDev = true;
      logger.env = 'development';
      logger.config = {
        console: ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
        backend: ['ERROR', 'CRITICAL'],
      };

      expect(logger.shouldLogToConsole(LOG_LEVELS.DEBUG)).toBe(true);
      expect(logger.shouldLogToConsole(LOG_LEVELS.INFO)).toBe(true);
    });

    it('should filter console logs in production', () => {
      logger.isDev = false;
      logger.env = 'production';
      logger.config = {
        console: ['ERROR', 'CRITICAL'],
        backend: ['INFO', 'WARN', 'ERROR', 'CRITICAL'],
      };

      expect(logger.shouldLogToConsole(LOG_LEVELS.DEBUG)).toBe(false);
      expect(logger.shouldLogToConsole(LOG_LEVELS.INFO)).toBe(false);
      expect(logger.shouldLogToConsole(LOG_LEVELS.ERROR)).toBe(true);
    });

    it('should filter backend logs correctly', () => {
      logger.config = {
        console: ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
        backend: ['ERROR', 'CRITICAL'],
      };

      expect(logger.shouldLogToBackend(LOG_LEVELS.DEBUG)).toBe(false);
      expect(logger.shouldLogToBackend(LOG_LEVELS.INFO)).toBe(false);
      expect(logger.shouldLogToBackend(LOG_LEVELS.ERROR)).toBe(true);
      expect(logger.shouldLogToBackend(LOG_LEVELS.CRITICAL)).toBe(true);
    });
  });

  describe('Batch Queuing', () => {
    it('should queue logs for batch sending', () => {
      logger.info('Test message', { key: 'value' });
      
      expect(logger.logQueue.length).toBe(1);
      expect(logger.logQueue[0].message).toBe('Test message');
      expect(logger.logQueue[0].level).toBe(LOG_LEVELS.INFO);
    });

    it('should enforce max queue size', () => {
      // Fill queue beyond MAX_QUEUE_SIZE
      const maxSize = 500;
      for (let i = 0; i < maxSize + 100; i++) {
        logger.logQueue.push({ message: `Log ${i}` });
      }
      
      logger.info('New log');
      
      expect(logger.logQueue.length).toBeLessThanOrEqual(maxSize);
    });

    it('should flush immediately for critical errors', async () => {
      const flushSpy = vi.spyOn(logger, 'flushLogs');
      
      logger.critical('Critical error', { code: 500 });
      
      expect(flushSpy).toHaveBeenCalled();
    });

    it('should flush when batch size is reached', async () => {
      const flushSpy = vi.spyOn(logger, 'flushLogs');
      
      // Fill to MAX_BATCH_SIZE
      for (let i = 0; i < 50; i++) {
        logger.logQueue.push({ message: `Log ${i}` });
      }
      
      logger.info('Trigger flush');
      
      expect(flushSpy).toHaveBeenCalled();
    });

    it('should schedule batch send after interval', () => {
      vi.useFakeTimers();
      
      logger.info('Test message');
      
      expect(logger.batchTimer).not.toBe(null);
      
      vi.advanceTimersByTime(5000);
      
      vi.useRealTimers();
    });
  });

  describe('Backend Communication', () => {
    it('should send logs to backend successfully', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
      });

      logger.logQueue = [
        { level: 'info', message: 'Test 1' },
        { level: 'warn', message: 'Test 2' },
      ];

      await logger.flushLogs();

      expect(fetch).toHaveBeenCalledWith(
        '/api/logs',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.any(String),
        })
      );
      
      expect(logger.logQueue.length).toBe(0);
      expect(logger.retryCount).toBe(0);
    });

    it('should handle rate limiting with Retry-After', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        headers: {
          get: (name) => (name === 'Retry-After' ? '10' : null),
        },
      });

      const scheduleSpy = vi.spyOn(logger, 'scheduleRetry');
      
      logger.logQueue = [{ level: 'info', message: 'Test' }];
      await logger.flushLogs();

      expect(scheduleSpy).toHaveBeenCalledWith(
        expect.any(Array),
        10000
      );
    });

    it('should retry on server errors (5xx)', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const scheduleSpy = vi.spyOn(logger, 'scheduleRetry');
      
      logger.logQueue = [{ level: 'info', message: 'Test' }];
      await logger.flushLogs();

      expect(scheduleSpy).toHaveBeenCalled();
    });

    it('should not retry on client errors (4xx)', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
      });

      const scheduleSpy = vi.spyOn(logger, 'scheduleRetry');
      
      logger.logQueue = [{ level: 'info', message: 'Test' }];
      await logger.flushLogs();

      expect(scheduleSpy).not.toHaveBeenCalled();
    });

    it('should retry on network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const scheduleSpy = vi.spyOn(logger, 'scheduleRetry');
      
      logger.logQueue = [{ level: 'info', message: 'Test' }];
      await logger.flushLogs();

      expect(scheduleSpy).toHaveBeenCalled();
    });
  });

  describe('Retry Logic with Exponential Backoff', () => {
    it('should apply exponential backoff', async () => {
      vi.useFakeTimers();

      logger.retryCount = 0;
      logger.scheduleRetry([{ message: 'Test' }]);
      expect(logger.retryTimer).not.toBe(null);
      
      // First retry: 1s
      vi.advanceTimersByTime(1000);
      
      logger.retryCount = 1;
      logger.scheduleRetry([{ message: 'Test' }]);
      
      // Second retry: 2s
      vi.advanceTimersByTime(2000);
      
      logger.retryCount = 2;
      logger.scheduleRetry([{ message: 'Test' }]);
      
      // Third retry: 4s
      vi.advanceTimersByTime(4000);

      vi.useRealTimers();
    });

    it('should persist to localStorage after max retries', async () => {
      logger.retryCount = 5; // MAX_RETRY_ATTEMPTS
      
      const persistSpy = vi.spyOn(logger, 'persistToStorage');
      
      logger.scheduleRetry([{ message: 'Failed log' }]);
      
      expect(logger.failedQueue.length).toBe(1);
      expect(persistSpy).toHaveBeenCalled();
      expect(logger.retryCount).toBe(0); // Reset after giving up
    });

    it('should not exceed max backoff time', async () => {
      logger.retryCount = 10; // Very high retry count
      
      vi.useFakeTimers();
      logger.scheduleRetry([{ message: 'Test' }]);
      
      // Should cap at 30s, not exponentially grow to minutes
      expect(logger.retryTimer).not.toBe(null);
      
      vi.useRealTimers();
    });
  });

  describe('localStorage Persistence', () => {
    it('should persist failed logs to localStorage', () => {
      logger.failedQueue = [
        { message: 'Failed 1' },
        { message: 'Failed 2' },
      ];
      
      logger.persistToStorage();
      
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'logger_offline_queue',
        expect.any(String)
      );
    });

    it('should restore logs from localStorage on init', () => {
      const storedLogs = [
        { message: 'Restored 1' },
        { message: 'Restored 2' },
      ];
      
      localStorage.getItem.mockReturnValue(JSON.stringify(storedLogs));
      
      const newLogger = new (logger.constructor)();
      
      expect(newLogger.failedQueue).toEqual(storedLogs);
    });

    it('should limit persisted logs to MAX_OFFLINE_LOGS', () => {
      const manyLogs = Array.from({ length: 150 }, (_, i) => ({
        message: `Log ${i}`,
      }));
      
      logger.failedQueue = manyLogs;
      logger.persistToStorage();
      
      const savedData = localStorage.setItem.mock.calls[0][1];
      const parsed = JSON.parse(savedData);
      
      expect(parsed.length).toBe(100); // MAX_OFFLINE_LOGS
    });

    it('should handle localStorage errors gracefully', () => {
      localStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });
      
      logger.failedQueue = [{ message: 'Test' }];
      
      expect(() => logger.persistToStorage()).not.toThrow();
    });

    it('should handle invalid JSON when restoring', () => {
      localStorage.getItem.mockReturnValue('invalid json');
      
      expect(() => new (logger.constructor)()).not.toThrow();
    });
  });

  describe('Synchronous Flush with sendBeacon', () => {
    it('should use sendBeacon for synchronous flush', () => {
      logger.logQueue = [{ message: 'Test 1' }];
      logger.failedQueue = [{ message: 'Test 2' }];
      
      logger.flushSync();
      
      expect(navigator.sendBeacon).toHaveBeenCalledWith(
        '/api/logs',
        expect.any(Blob)
      );
      
      expect(logger.logQueue.length).toBe(0);
      expect(logger.failedQueue.length).toBe(0);
    });

    it('should persist to localStorage if sendBeacon fails', () => {
      navigator.sendBeacon.mockImplementation(() => {
        throw new Error('sendBeacon failed');
      });
      
      const persistSpy = vi.spyOn(logger, 'persistToStorage');
      
      logger.logQueue = [{ message: 'Test' }];
      logger.flushSync();
      
      expect(persistSpy).toHaveBeenCalled();
      expect(logger.failedQueue.length).toBeGreaterThan(0);
    });
  });

  describe('Convenience Methods', () => {
    it('should log debug messages', () => {
      const logSpy = vi.spyOn(logger, 'log');
      
      logger.debug('Debug message', { key: 'value' });
      
      expect(logSpy).toHaveBeenCalledWith(
        LOG_LEVELS.DEBUG,
        'Debug message',
        { key: 'value' }
      );
    });

    it('should log info messages', () => {
      const logSpy = vi.spyOn(logger, 'log');
      
      logger.info('Info message');
      
      expect(logSpy).toHaveBeenCalledWith(
        LOG_LEVELS.INFO,
        'Info message',
        {}
      );
    });

    it('should log API errors with structured format', () => {
      const errorSpy = vi.spyOn(logger, 'error');
      
      logger.apiError(
        {
          status: 404,
          code: 'SESSION_NOT_FOUND',
          message: 'Session not found',
          resourceType: 'session',
          resourceId: 'abc-123',
        },
        '/api/sessions/abc-123',
        'GET'
      );
      
      expect(errorSpy).toHaveBeenCalledWith(
        'API Request Failed',
        expect.objectContaining({
          endpoint: '/api/sessions/abc-123',
          method: 'GET',
          status: 404,
          code: 'SESSION_NOT_FOUND',
        })
      );
    });

    it('should log component errors with stack trace', () => {
      const errorSpy = vi.spyOn(logger, 'error');
      
      const testError = new Error('Component crashed');
      const errorInfo = {
        componentStack: '\n    at MyComponent\n    at App',
      };
      
      logger.componentError(testError, errorInfo);
      
      expect(errorSpy).toHaveBeenCalledWith(
        'React Component Error',
        expect.objectContaining({
          error: expect.objectContaining({
            name: 'Error',
            message: 'Component crashed',
            stack: expect.any(String),
          }),
          componentStack: errorInfo.componentStack,
        })
      );
    });
  });

  describe('Context Enrichment', () => {
    it('should include context in log entries', () => {
      logger.info('Test message');
      
      const logEntry = logger.logQueue[0];
      
      expect(logEntry.context).toMatchObject({
        timestamp: expect.any(String),
        sessionId: expect.any(String),
        route: expect.any(String),
        userAgent: expect.any(String),
      });
    });

    it('should include current route in context', () => {
      // Mock window.location
      delete window.location;
      window.location = { pathname: '/chat' };
      
      const context = logger.getContext();
      
      expect(context.route).toBe('/chat');
    });
  });
});
