"use client";

import { useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Smartphone, Phone, Activity, Users, AlertCircle } from "lucide-react";
import { useDeviceStore } from "@/stores/device-store";
import { useSystemStore } from "@/stores/system-store";
import { useDevices } from "@/hooks/use-devices";
import { systemService } from "@/services/system.service";
import { formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const { devices } = useDeviceStore();
  const { stats, setStats } = useSystemStore();
  useDevices();

  useEffect(() => {
    systemService.getStats().then((r) => setStats(r.data)).catch(() => {});
  }, [setStats]);

  const connectedCount = useMemo(
    () => devices.filter((d) => d.is_connected).length,
    [devices],
  );

  const widgets = [
    {
      title: "Connected Devices",
      value: connectedCount,
      icon: Smartphone,
      description: "Active devices",
      color: "text-green-600",
    },
    {
      title: "Total Devices",
      value: devices.length,
      icon: Activity,
      description: "Registered devices",
      color: "text-blue-600",
    },
    {
      title: "Active Calls",
      value: stats?.active_calls ?? 0,
      icon: Phone,
      description: "Currently active",
      color: "text-purple-600",
    },
    {
      title: "Total Calls",
      value: stats?.total_calls ?? 0,
      icon: Users,
      description: "All time",
      color: "text-orange-600",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {widgets.map((widget) => {
          const Icon = widget.icon;
          return (
            <Card key={widget.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {widget.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${widget.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{widget.value}</div>
                <p className="text-xs text-muted-foreground">
                  {widget.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {devices.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground">
                <AlertCircle className="h-8 w-8" />
                <p className="text-sm font-medium">No device connected</p>
                <p className="text-xs">
                  Connect an Android phone via USB, enable USB debugging, then open Devices.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {devices.slice(0, 5).map((device) => (
                  <div
                    key={device.id}
                    className="flex items-center justify-between border-b pb-2 last:border-0"
                  >
                    <div>
                      <p className="text-sm font-medium">{device.device_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {device.manufacturer} {device.model}
                      </p>
                    </div>
                    <Badge
                      variant={
                        device.is_connected ? "success" : "secondary"
                      }
                    >
                      {device.is_connected ? "Connected" : "Disconnected"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">System Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Server Time</span>
              <span className="text-sm font-medium">
                {stats?.server_time
                  ? formatDate(stats.server_time)
                  : "Loading..."}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Python Version</span>
              <span className="text-sm font-medium">
                {stats?.python_version || "..."}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Platform</span>
              <span className="text-sm font-medium">
                {stats?.platform || "..."}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Total Users</span>
              <span className="text-sm font-medium">
                {stats?.total_users ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">System Logs</span>
              <span className="text-sm font-medium">
                {stats?.total_logs ?? 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
