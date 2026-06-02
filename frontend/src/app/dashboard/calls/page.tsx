"use client";

import { useEffect } from "react";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, formatDuration } from "@/lib/utils";
import { Phone, PhoneMissed, PhoneOff, Radio, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { callsService } from "@/services/calls.service";
import { useWebSocket } from "@/hooks/use-websocket";

export default function CallsPage() {
  const { data: callsData, isLoading, error, refetch } = useQuery({
    queryKey: ["calls"],
    queryFn: async () => {
      const response = await callsService.getAll();
      return response.data;
    },
  });

  useWebSocket(); // Enable real-time updates

  const calls = callsData || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Call Sessions</h2>
          <p className="text-sm text-muted-foreground">
            View and manage incoming call sessions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/dashboard/calls/live">
            <Button>
              <Radio className="mr-2 h-4 w-4" />
              Live Monitor
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Calls</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device</TableHead>
                <TableHead>Caller</TableHead>
                <TableHead>Number</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                    <RefreshCw className="mx-auto h-6 w-6 animate-spin mb-2" />
                    Loading calls...
                  </TableCell>
                </TableRow>
              ) : error ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-destructive">
                    Error loading calls: {error instanceof Error ? error.message : "Unknown error"}
                  </TableCell>
                </TableRow>
              ) : calls.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                    No call sessions found. Calls will appear here when devices receive incoming calls.
                  </TableCell>
                </TableRow>
              ) : (
                calls.map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="font-medium">
                      Device #{call.device_id}
                    </TableCell>
                    <TableCell>{call.caller_name || "Unknown"}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {call.caller_number || "N/A"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          call.call_status === "completed"
                            ? "success"
                            : call.call_status === "missed"
                              ? "destructive"
                              : "secondary"
                        }
                        className="flex w-fit items-center gap-1"
                      >
                        {call.call_status === "completed" ? (
                          <Phone className="h-3 w-3" />
                        ) : call.call_status === "missed" ? (
                          <PhoneMissed className="h-3 w-3" />
                        ) : (
                          <PhoneOff className="h-3 w-3" />
                        )}
                        {call.call_status.charAt(0).toUpperCase() +
                          call.call_status.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">
                      {call.start_time ? formatDate(call.start_time) : "N/A"}
                    </TableCell>
                    <TableCell>{formatDuration(call.duration)}</TableCell>
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
