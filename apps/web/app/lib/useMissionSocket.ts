"use client";

import { useEffect, useRef, useState } from "react";
import { missionSocketUrl } from "./api";

export interface MissionEvent {
  type: string;
  mission_id: string;
  data: Record<string, unknown>;
}

type ConnState = "connecting" | "open" | "closed";

// Subscribes to a mission's realtime feed (Redis-backed WebSocket on the API).
// Calls onEvent for each mission.* event; reconnects with backoff on drop
// (manual section 21: WebSocket reconnection supported).
export function useMissionSocket(
  missionId: string,
  token: string | null,
  onEvent: (e: MissionEvent) => void,
): ConnState {
  const [state, setState] = useState<ConnState>("connecting");
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!token) return;
    let closed = false;
    let ws: WebSocket | null = null;
    let retry = 0;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      setState("connecting");
      ws = new WebSocket(missionSocketUrl(missionId, token));

      ws.onopen = () => {
        retry = 0;
        setState("open");
      };
      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data) as MissionEvent;
          if (event.type === "connection.ready") return;
          onEventRef.current(event);
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setState("closed");
        if (closed) return;
        retry += 1;
        const delay = Math.min(1000 * 2 ** retry, 15000);
        timer = setTimeout(connect, delay);
      };
      ws.onerror = () => ws?.close();
    };

    connect();

    return () => {
      closed = true;
      clearTimeout(timer);
      ws?.close();
    };
  }, [missionId, token]);

  return state;
}
