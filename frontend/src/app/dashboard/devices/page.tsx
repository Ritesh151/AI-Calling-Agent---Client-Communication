"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDevices } from "@/hooks/use-devices";
import { formatDate } from "@/lib/utils";
import type { Device } from "@/types";
import {
  RefreshCw,
  Search,
  Trash2,
  Battery,
  BatteryFull,
  BatteryLow,
  BatteryMedium,
  Wifi,
  WifiOff,
  Monitor,
  MonitorOff,
  Activity,
  Plug,
  PlugZap,
  RotateCcw,
  Stethoscope,
  XCircle,
  CheckCircle2,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { Input } from "@/components/ui/input";

export default function DevicesPage() {
  const {
    devices,
    connectedDevices,
    isLoading,
    refetch,
    discover,
    isDiscovering,
    discoverResult,
    discoverError,
    deleteDevice,
    isDeleting,
    refreshDevice,
    isRefreshingDevice,
    reconnectDevice,
    isReconnecting,
    runDiagnostics,
    isRunningDiagnostics,
    diagnosticsResult,
    adbStatus,
  } = useDevices();

  const [search, setSearch] = useState("");
  const [showOnlyConnected, setShowOnlyConnected] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [actionMessage, setActionMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const [diagnosticsDeviceId, setDiagnosticsDeviceId] = useState<number | null>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [search]);

  const displayDevices = showOnlyConnected ? connectedDevices : devices;
  const filtered = debouncedSearch
    ? displayDevices.filter(
        (d) =>
          d.device_name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
          d.serial_number?.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
          d.manufacturer?.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
          d.model?.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
          d.android_version?.toLowerCase().includes(debouncedSearch.toLowerCase()),
      )
    : displayDevices;

  const onlineCount = devices.filter((d) => d.is_connected).length;
  const offlineCount = devices.filter((d) => !d.is_connected).length;

  const showMessage = useCallback((type: "success" | "error" | "info", text: string) => {
    setActionMessage({ type, text });
    setTimeout(() => setActionMessage(null), 5000);
  }, []);

  const handleDiscover = useCallback(() => {
    discover(undefined, {
      onSuccess: (result) => {
        const data = result?.data;
        if (data && Array.isArray(data)) {
          const found = data.filter((d: Record<string, unknown>) => !d.error);
          const errors = data.filter((d: Record<string, unknown>) => d.error);
          if (found.length > 0) {
            showMessage("success", `Discovered ${found.length} device(s)`);
          } else if (errors.length > 0) {
            showMessage("error", `Discovery failed: ${errors[0].error}`);
          } else {
            showMessage("info", "No devices found. Connect a device via USB and enable USB debugging.");
          }
        } else {
          showMessage("info", "Discovery completed");
        }
      },
      onError: (error) => {
        const msg = (error as Error)?.message || "Discovery failed";
        if (msg.includes("not found") || msg.includes("ADB")) {
          showMessage("error", "ADB is not installed or not found in PATH. Please install Android SDK Platform Tools.");
        } else if (msg.includes("unauthorized")) {
          showMessage("error", "Device is unauthorized. Check the device screen and approve USB debugging.");
        } else {
          showMessage("error", `Discovery failed: ${msg}`);
        }
      },
    });
  }, [discover, showMessage]);

  const handleDelete = useCallback(
    (device: Device) => {
      deleteDevice(device.id, {
        onSuccess: () => {
          showMessage("success", `Device "${device.device_name}" deleted`);
          setDeleteConfirmId(null);
        },
        onError: (error) => {
          showMessage("error", `Delete failed: ${(error as Error)?.message || "Unknown error"}`);
          setDeleteConfirmId(null);
        },
      });
    },
    [deleteDevice, showMessage],
  );

  const handleRefresh = useCallback(
    (device: Device) => {
      refreshDevice(device.id, {
        onSuccess: () => {
          showMessage("success", `Device "${device.device_name}" refreshed`);
        },
        onError: (error) => {
          showMessage("error", `Refresh failed: ${(error as Error)?.message || "Unknown error"}`);
        },
      });
    },
    [refreshDevice, showMessage],
  );

  const handleReconnect = useCallback(
    (device: Device) => {
      reconnectDevice(device.id, {
        onSuccess: (result) => {
          if (result?.data?.is_online) {
            showMessage("success", `Device "${device.device_name}" reconnected`);
          } else {
            showMessage("error", result?.data?.message || `Reconnect failed for "${device.device_name}"`);
          }
        },
        onError: (error) => {
          showMessage("error", `Reconnect failed: ${(error as Error)?.message || "Unknown error"}`);
        },
      });
    },
    [reconnectDevice, showMessage],
  );

  const handleDiagnostics = useCallback(
    (device: Device) => {
      setDiagnosticsDeviceId(device.id);
      runDiagnostics(device.id, {
        onSuccess: () => {
          showMessage("info", `Diagnostics completed for "${device.device_name}"`);
        },
        onError: (error) => {
          showMessage("error", `Diagnostics failed: ${(error as Error)?.message || "Unknown error"}`);
        },
      });
    },
    [runDiagnostics, showMessage],
  );

  const getBatteryIcon = (level: number | null | undefined) => {
    if (level === null || level === undefined)
      return <Activity className="h-4 w-4 text-muted-foreground" />;
    if (level >= 80) return <BatteryFull className="h-4 w-4 text-green-500" />;
    if (level >= 50)
      return <BatteryMedium className="h-4 w-4 text-yellow-500" />;
    if (level >= 20) return <BatteryLow className="h-4 w-4 text-orange-500" />;
    return <Battery className="h-4 w-4 text-red-500" />;
  };

  const getADBStatusDisplay = () => {
    if (!adbStatus) {
      return { label: "Unknown", color: "bg-gray-500", pulse: false };
    }
    switch (adbStatus.server_status) {
      case "active":
        return { label: "Active", color: "bg-green-500", pulse: true };
      case "disconnected":
        return { label: "Disconnected", color: "bg-red-500", pulse: false };
      case "error":
        return { label: "Error", color: "bg-red-500", pulse: false };
      case "unauthorized":
        return { label: "Unauthorized", color: "bg-yellow-500", pulse: true };
      default:
        return { label: adbStatus.server_status, color: "bg-gray-500", pulse: false };
    }
  };

  const adbDisplay = getADBStatusDisplay();

  return (
    <div className="space-y-4">
      {actionMessage && (
        <div
          className={`flex items-center gap-2 rounded-md px-4 py-3 text-sm ${
            actionMessage.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : actionMessage.type === "error"
                ? "bg-red-50 text-red-800 border border-red-200"
                : "bg-blue-50 text-blue-800 border border-blue-200"
          }`}
        >
          {actionMessage.type === "success" && <CheckCircle2 className="h-4 w-4 shrink-0" />}
          {actionMessage.type === "error" && <XCircle className="h-4 w-4 shrink-0" />}
          {actionMessage.type === "info" && <AlertTriangle className="h-4 w-4 shrink-0" />}
          <span className="flex-1">{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="shrink-0">
            <XCircle className="h-4 w-4" />
          </button>
        </div>
      )}

      {diagnosticsResult && diagnosticsDeviceId && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Diagnostics Result</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setDiagnosticsDeviceId(null)}>
                <XCircle className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-48">
              {JSON.stringify(diagnosticsResult.data, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Devices</h2>
          <p className="text-sm text-muted-foreground">
            Manage your connected Android devices with real-time health
            monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button onClick={handleDiscover} disabled={isDiscovering}>
            {isDiscovering ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Search className="mr-2 h-4 w-4" />
            )}
            {isDiscovering ? "Discovering..." : "Discover Devices"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{devices.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-green-500" />
              <span className="text-2xl font-bold">{onlineCount}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <span className="text-2xl font-bold">{offlineCount}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">ADB Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div
                className={`h-3 w-3 rounded-full ${adbDisplay.color} ${adbDisplay.pulse ? "animate-pulse" : ""}`}
              />
              <span className="text-sm font-medium">{adbDisplay.label}</span>
            </div>
            {adbStatus && (
              <div className="mt-1 text-xs text-muted-foreground">
                {adbStatus.connected_devices} device(s) connected
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-4">
        <Input
          placeholder="Search by name, serial, manufacturer, model, or Android version..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Button
          variant={showOnlyConnected ? "default" : "outline"}
          onClick={() => setShowOnlyConnected(!showOnlyConnected)}
        >
          {showOnlyConnected ? "Show All" : "Connected Only"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">All Devices</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device</TableHead>
                <TableHead>Serial</TableHead>
                <TableHead>Manufacturer</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Android</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Battery</TableHead>
                <TableHead>Screen</TableHead>
                <TableHead>Connection</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={11}
                    className="py-8 text-center text-muted-foreground"
                  >
                    {isLoading
                      ? "Loading devices..."
                      : showOnlyConnected
                        ? "No devices currently connected. Connect an Android device via USB and click 'Discover Devices'."
                        : "No devices found. Click 'Discover Devices' to scan for connected Android devices."}
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((device) => (
                  <TableRow key={device.id}>
                    <TableCell className="font-medium">
                      {device.device_name}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {device.serial_number || "N/A"}
                    </TableCell>
                    <TableCell>{device.manufacturer || "N/A"}</TableCell>
                    <TableCell>{device.model || "N/A"}</TableCell>
                    <TableCell>{device.android_version || "N/A"}</TableCell>
                    <TableCell>
                      <Badge
                        variant={device.is_connected ? "success" : "secondary"}
                      >
                        {device.is_connected ? "Connected" : "Disconnected"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {getBatteryIcon(device.battery_level)}
                        <span className="text-xs">
                          {device.battery_level !== null &&
                          device.battery_level !== undefined
                            ? `${device.battery_level}%`
                            : "N/A"}
                        </span>
                        {device.charging && (
                          <PlugZap className="h-3 w-3 text-green-500" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {device.screen_state ? (
                        <div className="flex items-center gap-1">
                          {device.screen_state === "on" ||
                          device.screen_state === "DREAM" ? (
                            <Monitor className="h-4 w-4 text-green-500" />
                          ) : (
                            <MonitorOff className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span className="text-xs">{device.screen_state}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          N/A
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {device.is_connected ? (
                          <Wifi className="h-4 w-4 text-green-500" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-muted-foreground" />
                        )}
                        {device.connection_type && (
                          <span className="text-xs text-muted-foreground">
                            {device.connection_type}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs">
                      {formatDate(device.last_seen)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Refresh device"
                          onClick={() => handleRefresh(device)}
                          disabled={isRefreshingDevice}
                        >
                          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshingDevice ? "animate-spin" : ""}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Reconnect device"
                          onClick={() => handleReconnect(device)}
                          disabled={isReconnecting}
                        >
                          <RotateCcw className={`h-3.5 w-3.5 ${isReconnecting ? "animate-spin" : ""}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Run diagnostics"
                          onClick={() => handleDiagnostics(device)}
                          disabled={isRunningDiagnostics && diagnosticsDeviceId === device.id}
                        >
                          <Stethoscope className={`h-3.5 w-3.5 ${isRunningDiagnostics && diagnosticsDeviceId === device.id ? "animate-spin" : ""}`} />
                        </Button>
                        {deleteConfirmId === device.id ? (
                          <div className="flex items-center gap-1">
                            <Button
                              variant="destructive"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => handleDelete(device)}
                              disabled={isDeleting}
                            >
                              {isDeleting ? "Deleting..." : "Confirm"}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => setDeleteConfirmId(null)}
                            >
                              <XCircle className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-destructive"
                            title="Delete device"
                            onClick={() => setDeleteConfirmId(device.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
