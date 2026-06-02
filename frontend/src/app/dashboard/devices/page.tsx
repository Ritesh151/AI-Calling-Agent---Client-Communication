"use client";

import { useState } from "react";
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
} from "lucide-react";
import { Input } from "@/components/ui/input";

export default function DevicesPage() {
  const { devices, connectedDevices, isLoading, refetch, discover, isDiscovering } = useDevices();
  const [search, setSearch] = useState("");
  const [showOnlyConnected, setShowOnlyConnected] = useState(false);

  // Filter devices based on connection status and search
  const displayDevices = showOnlyConnected ? connectedDevices : devices;
  const filtered = displayDevices.filter(
    (d) =>
      d.device_name.toLowerCase().includes(search.toLowerCase()) ||
      d.serial_number?.toLowerCase().includes(search.toLowerCase()) ||
      d.manufacturer?.toLowerCase().includes(search.toLowerCase()),
  );

  const onlineCount = devices.filter((d) => d.is_connected).length;
  const offlineCount = devices.filter((d) => !d.is_connected).length;

  const getBatteryIcon = (level: number | null | undefined) => {
    if (level === null || level === undefined)
      return <Activity className="h-4 w-4 text-muted-foreground" />;
    if (level >= 80) return <BatteryFull className="h-4 w-4 text-green-500" />;
    if (level >= 50)
      return <BatteryMedium className="h-4 w-4 text-yellow-500" />;
    if (level >= 20) return <BatteryLow className="h-4 w-4 text-orange-500" />;
    return <Battery className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="space-y-4">
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
          <Button onClick={() => discover()} disabled={isDiscovering}>
            <Search className="mr-2 h-4 w-4" />
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
              <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-medium">Active</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-4">
        <Input
          placeholder="Search devices..."
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
                          <span className="text-xs text-green-500">⚡</span>
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
                      {device.is_connected ? (
                        <Wifi className="h-4 w-4 text-green-500" />
                      ) : (
                        <WifiOff className="h-4 w-4 text-muted-foreground" />
                      )}
                    </TableCell>
                    <TableCell className="text-xs">
                      {formatDate(device.last_seen)}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
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
