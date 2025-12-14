import { useCallback, useEffect, useRef, useState } from "react";

export default function useStream() {
  const eventSourceRef = useRef(null);
  const timeoutRef = useRef(null);
  const [streaming, setStreaming] = useState(false);

  const abort = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setStreaming(false);
    }
  }, []);

  const start = useCallback((url, { onStart, onToken, onDone, onError, timeout = 300000 } = {}) => {
    abort();
    
    let hasReceivedData = false;
    let es;
    
    try {
      es = new EventSource(url);
    } catch (err) {
      onError?.({ 
        message: `Failed to create EventSource: ${err.message}`,
        error: "connection_failed" 
      });
      return () => {};
    }
    
    eventSourceRef.current = es;
    setStreaming(true);

    // Set timeout for stream inactivity
    if (timeout > 0) {
      timeoutRef.current = setTimeout(() => {
        if (eventSourceRef.current === es && !hasReceivedData) {
          const errorPayload = { 
            message: "Stream timeout: no data received", 
            error: "timeout" 
          };
          onError?.(errorPayload);
          abort();
        }
      }, timeout);
    }

    const parsePayload = (event) => {
      try {
        return JSON.parse(event.data);
      } catch {
        return event.data;
      }
    };

    const finish = (payload) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      if (eventSourceRef.current === es) {
        es.close();
        eventSourceRef.current = null;
        setStreaming(false);
      }
      onDone?.(payload);
    };

    const handleError = (payload, event) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      onError?.(payload, event);
      finish(payload);
    };

    es.addEventListener("start", (event) => {
      hasReceivedData = true;
      onStart?.(parsePayload(event));
    });

    es.addEventListener("token", (event) => {
      hasReceivedData = true;
      const payload = parsePayload(event);
      const token = typeof payload === "object" && payload !== null ? payload.token ?? payload?.data ?? "" : payload;
      if (token) onToken?.(token);
    });

    es.addEventListener("done", (event) => {
      hasReceivedData = true;
      finish(parsePayload(event));
    });

    es.addEventListener("error", (event) => {
      hasReceivedData = true;
      const payload = parsePayload(event);
      handleError(payload, event);
    });

    // Native EventSource error handler (network failures, connection issues)
    es.onerror = (event) => {
      // Check if this is a connection error vs. server-sent error event
      // ReadyState: 0=CONNECTING, 1=OPEN, 2=CLOSED
      if (es.readyState === EventSource.CLOSED) {
        const errorPayload = {
          message: hasReceivedData 
            ? "Connection closed unexpectedly" 
            : "Failed to connect to stream endpoint",
          error: "connection_error",
          readyState: es.readyState
        };
        handleError(errorPayload, event);
      } else if (es.readyState === EventSource.CONNECTING) {
        // Retry in progress, only error if we never got data
        if (!hasReceivedData) {
          const errorPayload = {
            message: "Unable to establish connection to stream",
            error: "connection_failed",
            readyState: es.readyState
          };
          handleError(errorPayload, event);
        }
      }
    };

    // Fallback for default message events
    es.onmessage = (event) => {
      hasReceivedData = true;
      const payload = parsePayload(event);
      if (typeof payload === "object" && payload !== null) {
        if (payload.type === "token") {
          onToken?.(payload.token);
        }
        if (payload.type === "meta" && payload.message === "stream_end") {
          finish(payload);
        }
      }
    };

    return () => {
      abort();
    };
  }, [abort]);

  useEffect(() => abort, [abort]);

  return { start, abort, streaming };
}
