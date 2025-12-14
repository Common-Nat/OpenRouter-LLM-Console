import { useCallback, useEffect, useRef, useState } from "react";

export default function useStream() {
  const eventSourceRef = useRef(null);
  const [streaming, setStreaming] = useState(false);

  const abort = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setStreaming(false);
    }
  }, []);

  const start = useCallback((url, { onStart, onToken, onDone, onError } = {}) => {
    abort();
    const es = new EventSource(url);
    eventSourceRef.current = es;
    setStreaming(true);

    const parsePayload = (event) => {
      try {
        return JSON.parse(event.data);
      } catch {
        return event.data;
      }
    };

    const finish = (payload) => {
      if (eventSourceRef.current === es) {
        es.close();
        eventSourceRef.current = null;
        setStreaming(false);
      }
      onDone?.(payload);
    };

    es.addEventListener("start", (event) => {
      onStart?.(parsePayload(event));
    });

    es.addEventListener("token", (event) => {
      const payload = parsePayload(event);
      const token = typeof payload === "object" && payload !== null ? payload.token ?? payload?.data ?? "" : payload;
      if (token) onToken?.(token);
    });

    es.addEventListener("done", (event) => {
      finish(parsePayload(event));
    });

    es.addEventListener("error", (event) => {
      const payload = parsePayload(event);
      onError?.(payload, event);
      finish(payload);
    });

    // Fallback for default message events
    es.onmessage = (event) => {
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
