"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { systemService, type SystemDiagnostics } from "@/services/system.service";

export default function DiagnosticsPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<SystemDiagnostics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await systemService.getDiagnostics();
      setData(response.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Diagnostics request failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  const statusIcon = (status?: string) => {
    if (status === "healthy") return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    if (status === "unhealthy") return <XCircle className="h-5 w-5 text-red-500" />;
    return <AlertCircle className="h-5 w-5 text-yellow-500" />;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Diagnostics</h2>
          <p className="text-sm text-muted-foreground">
            Live status from backend health checks (refreshes every 10s)
          </p>
        </div>
        <Button onClick={load} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="text-sm">Database</CardTitle></CardHeader>
          <CardContent className="flex items-center justify-between">
            {statusIcon(data?.database?.status)}
            <Badge variant={data?.database?.status === "healthy" ? "default" : "destructive"}>
              {data?.database?.status || "unknown"}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Redis</CardTitle></CardHeader>
          <CardContent className="flex items-center justify-between">
            {statusIcon(data?.redis?.status)}
            <Badge variant={data?.redis?.status === "healthy" ? "default" : "destructive"}>
              {data?.redis?.status || "unknown"}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">ADB</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm">Server: {String(data?.adb?.server_running ?? "—")}</p>
            <p className="text-sm">Devices: {String(data?.adb?.devices_found ?? 0)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Devices (ADB verified)</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{data?.devices?.connected ?? 0}</p>
            <p className="text-xs text-muted-foreground">ADB found: {data?.devices?.adb_found ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">WebSocket</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm">Server connections: {data?.websocket?.active_connections ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Auto Answer</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>Enabled: {String(data?.auto_answer?.enabled ?? false)}</p>
            <p>Device ready: {String(data?.auto_answer?.device_ready ?? false)}</p>
            <p>Can answer: {String(data?.auto_answer?.can_answer ?? false)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Call Detection</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm">
              Poll interval: {data?.call_detection?.poll_interval_seconds ?? "—"}s
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">AI</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>Provider: {data?.ai?.provider || "—"}</p>
            <p>Configured: {String(data?.ai?.configured ?? false)}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Background Workers</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-3">
            {data?.workers &&
              Object.entries(data.workers).map(([name, status]) => (
                <div key={name} className="flex items-center justify-between rounded border p-2">
                  <span>{name}</span>
                  <Badge variant={status.running ? "default" : "secondary"}>
                    {status.running ? "Running" : "Stopped"}
                  </Badge>
                </div>
              ))}
            {!data?.workers && (
              <p className="text-muted-foreground">No worker data yet</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
