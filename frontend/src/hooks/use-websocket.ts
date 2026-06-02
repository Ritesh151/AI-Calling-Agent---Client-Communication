"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useDeviceStore } from "@/stores/device-store";
import { useSystemStore } from "@/stores/system-store";
import { useQueryClient } from "@tanstack/react-query";
import { resolveWebSocketUrl, WS_READY_STATE } from "@/lib/ws-url";

type EventHandler = (data: unknown) => void;

export type WSConnectionStatus =
  | "CONNECTED"
  | "CONNECTING"
  | "RECONNECTING"
  | "DISCONNECTED"
  | "FAILED";

function logWsDiagnostics(
  phase: string,
  details: Record<string, unknown>,
): void {
  console.warn(`[WebSocket] ${phase}`, details);
}

export function useWebSocket(enabled = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Map<string, EventHandler[]>>(new Map());
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimeoutRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const lastCloseRef = useRef<{ code: number; reason: string; wasClean: boolean } | null>(
    null,
  );
  const mountedRef = useRef(true);
  const maxReconnectAttempts = 10;
  const queryClient = useQueryClient();

  const [connectionStatus, setConnectionStatus] =
    useState<WSConnectionStatus>("DISCONNECTED");
  const [lastMessage, setLastMessage] = useState<unknown>(null);
  const [backendHealth, setBackendHealth] = useState(false);
  const [wsUrl, setWsUrl] = useState<string>("");

  const deviceStoreRef = useRef(useDeviceStore.getState());
  const systemStoreRef = useRef(useSystemStore.getState());

  useEffect(() => {
    const unsubDevice = useDeviceStore.subscribe((state) => {
      deviceStoreRef.current = state;
    });
    const unsubSystem = useSystemStore.subscribe((state) => {
      systemStoreRef.current = state;
    });
    return () => {
      unsubDevice();
      unsubSystem();
    };
  }, []);

  const subscribe = useCallback((eventType: string, handler: EventHandler) => {
    if (!handlersRef.current.has(eventType)) {
      handlersRef.current.set(eventType, []);
    }
    handlersRef.current.get(eventType)!.push(handler);
    return () => {
      const handlers = handlersRef.current.get(eventType);
      if (handlers) {
        const idx = handlers.indexOf(handler);
        if (idx >= 0) handlers.splice(idx, 1);
      }
    };
  }, []);

  const clearHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearInterval(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback((ws: WebSocket) => {
    clearHeartbeat();
    heartbeatTimeoutRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000);
  }, [clearHeartbeat]);

  const handleMessage = useCallback(
    (raw: string) => {
      const message = JSON.parse(raw);
      setLastMessage(message);

      if (message.type === "pong" || message.type === "ping") {
        return;
      }

      const handlers = handlersRef.current.get(message.type) || [];
      handlers.forEach((handler) => handler(message.data || message));

      const { updateDevice, setDevices, setConnectedDevices } = deviceStoreRef.current;
      const { setStats } = systemStoreRef.current;

      switch (message.type) {
        case "device_connected":
          queryClient.invalidateQueries({ queryKey: ["devices"] });
          break;
        case "device_disconnected":
          if (message.data?.device_id) {
            updateDevice(message.data.device_id, {
              is_connected: false,
              status: "disconnected",
            });
            queryClient.invalidateQueries({ queryKey: ["devices"] });
            queryClient.invalidateQueries({ queryKey: ["devices", "connected"] });
          }
          break;
        case "devices_synced":
          queryClient.invalidateQueries({ queryKey: ["devices"] });
          queryClient.invalidateQueries({ queryKey: ["devices", "connected"] });
          if (message.data?.connected_count === 0) {
            setDevices([]);
            setConnectedDevices([]);
          }
          break;
        case "heartbeat":
        case "device_heartbeat":
          if (message.data?.device_id) {
            updateDevice(message.data.device_id, {
              battery_level: message.data.battery_level,
              charging: message.data.charging,
              screen_state: message.data.screen_state,
              last_seen: message.data.timestamp || new Date().toISOString(),
              is_connected: true,
            });
          }
          break;
        case "incoming_call":
        case "call_answered":
        case "call_ended":
        case "call_started":
        case "ai_answer_started":
        case "ai_answer_completed":
          queryClient.invalidateQueries({ queryKey: ["calls"] });
          break;
        case "recording_stopped":
          queryClient.invalidateQueries({ queryKey: ["recordings"] });
          break;
        case "transcription_complete":
          queryClient.invalidateQueries({ queryKey: ["transcripts"] });
          break;
        case "settings_updated":
          queryClient.invalidateQueries({ queryKey: ["settings"] });
          break;
        case "system_stats":
          if (message.data) setStats(message.data);
          break;
      }
    },
    [queryClient],
  );

  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current) return;

    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    if (!token) {
      console.info("[WebSocket] Skipped — no access_token in localStorage");
      setConnectionStatus("DISCONNECTED");
      return;
    }

    // Prevent duplicate connections
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    const url = resolveWebSocketUrl();
    setWsUrl(url);
    setConnectionStatus("CONNECTING");

    console.info("[WebSocket] Connecting", {
      url,
      pageOrigin: typeof window !== "undefined" ? window.location.origin : "",
      apiUrl: process.env.NEXT_PUBLIC_API_URL,
      configuredWsUrl: process.env.NEXT_PUBLIC_WS_URL,
    });

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      console.info("[WebSocket] OPEN — handshake 101 succeeded", { url });
      setConnectionStatus("CONNECTED");
      setBackendHealth(true);
      reconnectAttemptsRef.current = 0;
      startHeartbeat(ws);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      handleMessage(event.data);
    };

    ws.onclose = (event) => {
      if (!mountedRef.current) return;

      lastCloseRef.current = {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      };

      console.warn("[WebSocket] CLOSE", {
        url,
        code: event.code,
        reason: event.reason || "(empty)",
        wasClean: event.wasClean,
        readyState: WS_READY_STATE[ws.readyState] ?? ws.readyState,
        hint:
          event.code === 1006
            ? "Abnormal closure — server unreachable, wrong host/port, or connection dropped before handshake completed"
            : undefined,
      });

      clearHeartbeat();
      setConnectionStatus("DISCONNECTED");
      setBackendHealth(false);
      wsRef.current = null;

      if (
        reconnectAttemptsRef.current < maxReconnectAttempts &&
        event.code !== 1000 &&
        enabled
      ) {
        setConnectionStatus("RECONNECTING");
        const delay = Math.min(
          1000 * 2 ** reconnectAttemptsRef.current,
          30000,
        );
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connect();
        }, delay);
      } else if (event.code !== 1000) {
        setConnectionStatus("FAILED");
      }
    };

    ws.onerror = () => {
      // Browser fires Event with no enumerable fields — logging {} is misleading.
      // Real diagnostics are on onclose (code 1006) and onopen failure above.
      logWsDiagnostics("ERROR (handshake or transport failure)", {
        url,
        readyState: WS_READY_STATE[ws.readyState] ?? ws.readyState,
        lastClose: lastCloseRef.current,
        pageOrigin: typeof window !== "undefined" ? window.location.origin : "",
        tokenPresent: !!token,
        note: "Check Network tab → WS → Status must be 101 Switching Protocols",
      });
      setConnectionStatus("FAILED");
      setBackendHealth(false);
    };
  }, [enabled, handleMessage, startHeartbeat, clearHeartbeat]);

  useEffect(() => {
    mountedRef.current = true;

    if (enabled) {
      console.info("[WebSocket] Lifecycle mount", {
        WS_URL: resolveWebSocketUrl(),
        windowLocation:
          typeof window !== "undefined" ? window.location.href : "ssr",
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
        NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
      });
      connect();
    }

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      clearHeartbeat();
      if (wsRef.current) {
        wsRef.current.close(1000, "component unmount");
        wsRef.current = null;
      }
      setConnectionStatus("DISCONNECTED");
    };
  }, [enabled]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    if (wsRef.current) {
      wsRef.current.close(1000, "manual reconnect");
      wsRef.current = null;
    }
    connect();
  }, [connect]);

  const updateBackendHealth = useCallback((healthy: boolean) => {
    setBackendHealth(healthy);
  }, []);

  return {
    subscribe,
    connectionStatus,
    reconnect,
    lastMessage,
    backendHealth,
    updateBackendHealth,
    wsUrl,
  };
}
