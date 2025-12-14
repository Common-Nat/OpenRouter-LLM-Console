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

  const start = useCallback((url, { onToken, onDone, onError } = {}) => {
    abort();
    const es = new EventSource(url);
    eventSourceRef.current = es;
    setStreaming(true);

    const finish = () => {
      if (eventSourceRef.current === es) {
        es.close();
        eventSourceRef.current = null;
        setStreaming(false);
      }
      onDone?.();
    };

    es.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "token") {
          onToken?.(msg.token);
        } else if ((msg.type === "meta" && msg.message === "stream_end") || es.readyState === EventSource.CLOSED) {
          finish();
        }
      } catch {
        // ignore parsing errors
      }
    };

    es.onerror = (event) => {
      onError?.(event);
      finish();
    };

    return () => {
      abort();
    };
  }, [abort]);

  useEffect(() => abort, [abort]);

  return { start, abort, streaming };
}
