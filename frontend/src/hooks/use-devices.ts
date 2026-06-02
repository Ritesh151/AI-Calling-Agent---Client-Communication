"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { devicesService } from "@/services/devices.service";
import { useDeviceStore } from "@/stores/device-store";

export function useDevices() {
  const queryClient = useQueryClient();
  const { setDevices, setConnectedDevices, setIsLoading } = useDeviceStore();

  const devicesQuery = useQuery({
    queryKey: ["devices"],
    queryFn: async () => {
      setIsLoading(true);
      try {
        const response = await devicesService.getAll();
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

  const connectedQuery = useQuery({
    queryKey: ["devices", "connected"],
    queryFn: async () => {
      const response = await devicesService.getConnected();
      setConnectedDevices(response.data);
      return response.data;
    },
    refetchInterval: 30000,
    refetchIntervalInBackground: false,
  });

  const discoverMutation = useMutation({
    mutationFn: () => devicesService.discover(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => devicesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  return {
    devices: devicesQuery.data ?? [],
    connectedDevices: connectedQuery.data ?? [],
    isLoading: devicesQuery.isLoading,
    error: devicesQuery.error,
    refetch: async () => {
      await Promise.all([devicesQuery.refetch(), connectedQuery.refetch()]);
    },
    discover: discoverMutation.mutate,
    isDiscovering: discoverMutation.isPending,
    deleteDevice: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  };
}
