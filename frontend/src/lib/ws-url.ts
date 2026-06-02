/**
 * Resolve WebSocket URL at runtime.
 *
 * Root cause addressed: NEXT_PUBLIC_WS_URL often hardcodes `localhost` while the
 * browser is opened via 127.0.0.1, a LAN IP, or a hostname — the handshake
 * then targets the wrong host and fails with an empty browser Event in onerror.
 */
export function resolveWebSocketUrl(): string {
  const configured = process.env.NEXT_PUBLIC_WS_URL?.trim();
  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

  if (typeof window === "undefined") {
    return configured || `${apiBase.replace(/^http/, "ws")}/ws`;
  }

  if (configured) {
    try {
      const wsUrl = new URL(configured);
      const apiUrl = new URL(apiBase);
      const pageHost = window.location.hostname;
      const configHost = wsUrl.hostname;

      const isLocalConfig =
        configHost === "localhost" || configHost === "127.0.0.1";
      const pageIsLocal =
        pageHost === "localhost" || pageHost === "127.0.0.1";

      if (isLocalConfig && !pageIsLocal) {
        wsUrl.hostname = pageHost;
        wsUrl.port = apiUrl.port || wsUrl.port || "8000";
        return wsUrl.toString();
      }

      return configured;
    } catch {
      // fall through to API-derived URL
    }
  }

  const apiUrl = new URL(apiBase);
  const protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${apiUrl.host}/ws`;
}

export const WS_READY_STATE: Record<number, string> = {
  0: "CONNECTING",
  1: "OPEN",
  2: "CLOSING",
  3: "CLOSED",
};
