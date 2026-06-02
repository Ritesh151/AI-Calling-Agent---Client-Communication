"use client";

import { useCallback, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { devicesService, type DeviceListParams } from "@/services/devices.service";
import { useDeviceStore } from "@/stores/device-store";

export function useDevices() {
  const queryClient = useQueryClient();
  const { setDevices, setConnectedDevices, setIsLoading, setADBStatus } = useDeviceStore();

  const devicesQuery = useQuery({
    queryKey: ["devices"],
    queryFn: async () => {
      setIsLoading(true);
      try {
        const response = await devicesService.getAll({ sync: true, adb_present_only: false });
        setDevices(response.data);
        setConnectedDevices(response.data.filter((d) => d.is_connected));
        return response.data;
      } finally {
        setIsLoading(false);
      }
    },
    refetchInterval: 15000,
    refetchIntervalInBackground: false,
  });

  const adbStatusQuery = useQuery({
    queryKey: ["devices", "adb-status"],
    queryFn: async () => {
      const response = await devicesService.getADBStatus();
      setADBStatus(response.data);
      return response.data;
    },
    refetchInterval: 10000,
    refetchIntervalInBackground: false,
  });

  const searchDevices = useCallback(
    async (params: DeviceListParams) => {
      const response = await devicesService.getAll({ ...params, sync: false, adb_present_only: false });
      return response.data;
    },
    [],
  );

  const discoverMutation = useMutation({
    mutationFn: () => devicesService.discover(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["devices", "adb-status"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => devicesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const refreshDeviceMutation = useMutation({
    mutationFn: (id: number) => devicesService.refreshDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const reconnectDeviceMutation = useMutation({
    mutationFn: (id: number) => devicesService.reconnectDevice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const diagnosticsMutation = useMutation({
    mutationFn: (id: number) => devicesService.runDiagnostics(id),
  });

  const syncMutation = useMutation({
    mutationFn: () => devicesService.sync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
      queryClient.invalidateQueries({ queryKey: ["devices", "adb-status"] });
    },
  });

  useEffect(() => {
    setADBStatus(adbStatusQuery.data ?? null);
  }, [adbStatusQuery.data, setADBStatus]);

  return {
    devices: devicesQuery.data ?? [],
    connectedDevices: useDeviceStore((s) => s.connectedDevices),
    isLoading: devicesQuery.isLoading,
    error: devicesQuery.error,
    refetch: async () => {
      await Promise.all([
        devicesQuery.refetch(),
        adbStatusQuery.refetch(),
      ]);
    },
    discover: discoverMutation.mutate,
    isDiscovering: discoverMutation.isPending,
    discoverResult: discoverMutation.data,
    discoverError: discoverMutation.error,
    deleteDevice: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
    refreshDevice: refreshDeviceMutation.mutate,
    isRefreshingDevice: refreshDeviceMutation.isPending,
    reconnectDevice: reconnectDeviceMutation.mutate,
    isReconnecting: reconnectDeviceMutation.isPending,
    runDiagnostics: diagnosticsMutation.mutate,
    isRunningDiagnostics: diagnosticsMutation.isPending,
    diagnosticsResult: diagnosticsMutation.data,
    sync: syncMutation.mutate,
    isSyncing: syncMutation.isPending,
    adbStatus: adbStatusQuery.data ?? null,
    searchDevices,
  };
}
