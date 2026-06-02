import { create } from "zustand";
import type { ADBStatus, Device } from "@/types";

interface DeviceState {
  devices: Device[];
  connectedDevices: Device[];
  selectedDevice: Device | null;
  isLoading: boolean;
  adbStatus: ADBStatus | null;
  setDevices: (devices: Device[]) => void;
  setConnectedDevices: (devices: Device[]) => void;
  setSelectedDevice: (device: Device | null) => void;
  setIsLoading: (value: boolean) => void;
  setADBStatus: (status: ADBStatus | null) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: number, data: Partial<Device>) => void;
  removeDevice: (id: number) => void;
}

export const useDeviceStore = create<DeviceState>((set) => ({
  devices: [],
  connectedDevices: [],
  selectedDevice: null,
  isLoading: false,
  adbStatus: null,
  setDevices: (devices) => set({ devices }),
  setConnectedDevices: (devices) => set({ connectedDevices: devices }),
  setSelectedDevice: (device) => set({ selectedDevice: device }),
  setIsLoading: (value) => set({ isLoading: value }),
  setADBStatus: (status) => set({ adbStatus: status }),
  addDevice: (device) =>
    set((state) => ({ devices: [...state.devices, device] })),
  updateDevice: (id, data) =>
    set((state) => ({
      devices: state.devices.map((d) => (d.id === id ? { ...d, ...data } : d)),
      connectedDevices: state.connectedDevices.map((d) =>
        d.id === id ? { ...d, ...data } : d,
      ),
    })),
  removeDevice: (id) =>
    set((state) => ({
      devices: state.devices.filter((d) => d.id !== id),
      connectedDevices: state.connectedDevices.filter((d) => d.id !== id),
    })),
}));
