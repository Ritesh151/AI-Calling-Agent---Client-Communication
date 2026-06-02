"use client";

import { useWebSocket } from "@/hooks/use-websocket";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";

export function DebugPanel() {
  const {
    connectionStatus,
    lastMessage,
    backendHealth,
    updateBackendHealth,
  } = useWebSocket();
  const [backendReachable, setBackendReachable] = useState<boolean>(false);
  const [wsUrl, setWsUrl] = useState<string>(process.env.NEXT_PUBLIC_WS_URL || "");

  useEffect(() => {
    // Check backend health via HTTP
    const checkBackend = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
        const data = await response.json();
        setBackendReachable(response.ok);
        updateBackendHealth(response.ok);
      } catch (error) {
        setBackendReachable(false);
        updateBackendHealth(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [updateBackendHealth]);

  return (
    <div className="fixed bottom-4 right-4 w-80 border border-muted-background bg-background/90 backdrop-blur">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold">WebSocket Debug</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span>URL:</span>
            <span className="font-mono">{wsUrl}</span>
          </div>
          <div className="flex justify-between">
            <span>Status:</span>
            <span>
              <Badge
                variant={connectionStatus === "CONNECTED" ? "success" : connectionStatus === "CONNECTING" || connectionStatus === "RECONNECTING" ? "warning" : "destructive"}
              >
                {connectionStatus}
              </Badge>
            </span>
          </div>
          <div className="flex justify-between">
            <span>Backend:</span>
            <span>
              <Badge variant={backendReachable ? "success" : "destructive"}>
                {backendReachable ? "Reachable" : "Unreachable"}
              </Badge>
            </span>
          </div>
          <div className="flex justify-between">
            <span>Last Msg:</span>
            <span className="font-mono truncate max-w-xs">
              {lastMessage ? JSON.stringify(lastMessage).substring(0, 50) : "None"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}