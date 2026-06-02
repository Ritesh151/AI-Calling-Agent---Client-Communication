import { create } from "zustand";
import type { Device } from "@/types";

interface DeviceState {
  devices: Device[];
  connectedDevices: Device[];
  selectedDevice: Device | null;
  isLoading: boolean;
  setDevices: (devices: Device[]) => void;
  setConnectedDevices: (devices: Device[]) => void;
  setSelectedDevice: (device: Device | null) => void;
  setIsLoading: (value: boolean) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: number, data: Partial<Device>) => void;
  removeDevice: (id: number) => void;
}

export const useDeviceStore = create<DeviceState>((set) => ({
  devices: [],
  connectedDevices: [],
  selectedDevice: null,
  isLoading: false,
  setDevices: (devices) => set({ devices }),
  setConnectedDevices: (devices) => set({ connectedDevices: devices }),
  setSelectedDevice: (device) => set({ selectedDevice: device }),
  setIsLoading: (value) => set({ isLoading: value }),
  addDevice: (device) =>
    set((state) => ({ devices: [...state.devices, device] })),
  updateDevice: (id, data) =>
    set((state) => ({
      devices: state.devices.map((d) => (d.id === id ? { ...d, ...data } : d)),
    })),
  removeDevice: (id) =>
    set((state) => ({
      devices: state.devices.filter((d) => d.id !== id),
    })),
}));
