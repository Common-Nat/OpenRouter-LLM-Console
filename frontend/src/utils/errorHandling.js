/**
 * Example frontend error handling for structured API responses
 * 
 * This demonstrates how to leverage the new error format in React/JavaScript
 */

// Error code constants (match backend)
export const ERROR_CODES = {
  SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',
  PROFILE_NOT_FOUND: 'PROFILE_NOT_FOUND',
  DOCUMENT_NOT_FOUND: 'DOCUMENT_NOT_FOUND',
  MESSAGE_NOT_FOUND: 'MESSAGE_NOT_FOUND',
  USAGE_LOG_NOT_FOUND: 'USAGE_LOG_NOT_FOUND',
  MISSING_API_KEY: 'MISSING_API_KEY',
  MISSING_FILENAME: 'MISSING_FILENAME',
  FILE_SAVE_FAILED: 'FILE_SAVE_FAILED',
  FILE_DELETE_FAILED: 'FILE_DELETE_FAILED',
  OPENROUTER_ERROR: 'OPENROUTER_ERROR',
  STREAM_ERROR: 'STREAM_ERROR',
};

/**
 * Parse structured error from API response
 * @param {Response} response - Fetch API response
 * @returns {Promise<object>} Parsed error object
 */
export async function parseApiError(response) {
  try {
    const error = await response.json();
    return {
      status: response.status,
      code: error.error_code,
      message: error.message,
      resourceType: error.resource_type,
      resourceId: error.resource_id,
      details: error.details,
    };
  } catch {
    // Fallback for non-JSON responses
    return {
      status: response.status,
      code: 'UNKNOWN_ERROR',
      message: response.statusText || 'An error occurred',
    };
  }
}

/**
 * Generate user-friendly error message based on error code
 * @param {object} error - Parsed error object
 * @returns {string} User-friendly message
 */
export function getUserFriendlyMessage(error) {
  const { code, resourceId, resourceType, message } = error;

  switch (code) {
    case ERROR_CODES.SESSION_NOT_FOUND:
      return `Session ${resourceId} was not found. It may have been deleted or expired.`;
    
    case ERROR_CODES.PROFILE_NOT_FOUND:
      return `Profile ${resourceId} was not found. Please select a different profile.`;
    
    case ERROR_CODES.DOCUMENT_NOT_FOUND:
      return `Document "${resourceId}" was not found. It may have been deleted.`;
    
    case ERROR_CODES.MISSING_API_KEY:
      return 'API key is not configured. Please contact your administrator.';
    
    case ERROR_CODES.FILE_SAVE_FAILED:
      return `Failed to save file. ${error.details?.error || 'Please try again.'}`;
    
    case ERROR_CODES.FILE_DELETE_FAILED:
      return `Failed to delete ${resourceType} "${resourceId}". ${error.details?.error || ''}`;
    
    // Fallback to server message
    default:
      return message || 'An error occurred. Please try again.';
  }
}

/**
 * Handle API error with automatic retry for specific error codes
 * @param {object} error - Parsed error object
 * @param {Function} retryFn - Function to retry
 * @returns {boolean} True if retry was attempted
 */
export async function handleErrorWithRetry(error, retryFn) {
  const retryableCodes = [
    ERROR_CODES.OPENROUTER_ERROR,
    ERROR_CODES.STREAM_ERROR,
  ];

  if (retryableCodes.includes(error.code)) {
    console.log(`Retrying after error: ${error.code}`);
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
    return await retryFn();
  }

  return false;
}

/**
 * Example usage in a React component
 */
export async function exampleApiCall(sessionId) {
  try {
    const response = await fetch(`/api/sessions/${sessionId}`);
    
    if (!response.ok) {
      const error = await parseApiError(response);
      
      // Show user-friendly message
      const message = getUserFriendlyMessage(error);
      alert(message);
      
      // Log structured error for debugging
      console.error('API Error:', {
        code: error.code,
        status: error.status,
        resource: `${error.resourceType}:${error.resourceId}`,
        details: error.details,
      });
      
      // Handle specific errors
      switch (error.code) {
        case ERROR_CODES.SESSION_NOT_FOUND:
          // Redirect to sessions list
          window.location.href = '/sessions';
          break;
        
        case ERROR_CODES.MISSING_API_KEY:
          // Show configuration modal
          showConfigModal();
          break;
        
        default:
          // Generic error handling
          break;
      }
      
      return null;
    }
    
    return await response.json();
  } catch (err) {
    console.error('Network error:', err);
    alert('Network error. Please check your connection.');
    return null;
  }
}

/**
 * Example SSE error handler
 */
export function createEventSourceWithErrorHandling(url) {
  const eventSource = new EventSource(url);
  
  eventSource.addEventListener('error', async (event) => {
    if (event.data) {
      try {
        const error = JSON.parse(event.data);
        const message = getUserFriendlyMessage({
          code: error.error_code,
          message: error.message,
          resourceType: error.resource_type,
          resourceId: error.resource_id,
          details: error.details,
        });
        
        console.error('Stream error:', message);
        alert(message);
        
        // Handle specific streaming errors
        if (error.error_code === ERROR_CODES.SESSION_NOT_FOUND) {
          eventSource.close();
          window.location.href = '/sessions';
        }
      } catch {
        console.error('Failed to parse stream error');
      }
    }
  });
  
  return eventSource;
}

/**
 * Example hook for React error boundary
 */
export function useApiErrorHandler() {
  const handleError = async (response) => {
    const error = await parseApiError(response);
    const message = getUserFriendlyMessage(error);
    
    // Could integrate with toast notifications, error tracking, etc.
    return { error, message };
  };
  
  return { handleError };
}
