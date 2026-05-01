import { useCallback, useEffect, useRef, useState } from "react";
import type { WSEvent } from "../types";

interface UseWebSocketOptions {
  conversationId: string;
  customerId: string;
  onEvent?: (event: WSEvent) => void;
}

export function useWebSocket({ conversationId, customerId, onEvent }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/chat/${conversationId}?customer_id=${customerId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data);
        onEventRef.current?.(data);
      } catch {
        // ignore parse errors
      }
    };

    return () => {
      ws.close();
    };
  }, [conversationId, customerId]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", content }));
    }
  }, []);

  return { connected, sendMessage };
}
