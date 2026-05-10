"use client";

import { useEffect, useRef, useCallback } from "react";
import { AgentEvent } from "@/lib/types";

interface StreamConsumerProps {
  sessionId: string;
  token: string;
  onEvent: (event: AgentEvent) => void;
  onFinalOutput: (content: string) => void;
  onDone: () => void;
  onError: () => void;
}

/**
 * Headless component that manages an SSE connection to the NexusMind backend.
 * Uses the `?token=` query param because the native EventSource API cannot
 * send custom Authorization headers.
 *
 * Renders nothing — all data is surfaced through callbacks.
 */
export default function StreamConsumer({
  sessionId,
  token,
  onEvent,
  onFinalOutput,
  onDone,
  onError,
}: StreamConsumerProps) {
  const esRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    // Close any existing connection first
    esRef.current?.close();

    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/stream/${sessionId}?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e: MessageEvent) => {
      let event: AgentEvent;
      try {
        event = JSON.parse(e.data) as AgentEvent;
      } catch {
        return; // Ignore malformed frames (e.g. ping events)
      }

      onEvent(event);

      if (event.type === "FINAL_OUTPUT") {
        onFinalOutput(event.data?.final_content ?? "");
        onDone();
        es.close();
      }

      if (event.type === "PIPELINE_ERROR" || event.type === "ERROR") {
        onError();
        es.close();
      }
    };

    es.onerror = () => {
      es.close();
      onError();
    };
  }, [sessionId, token, onEvent, onFinalOutput, onDone, onError]);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
    };
  }, [connect]);

  return null;
}
