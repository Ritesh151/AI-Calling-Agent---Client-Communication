import { create } from "zustand";
import type { SystemStats } from "@/types";

interface SystemState {
  stats: SystemStats | null;
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  isLoading: boolean;
  setStats: (stats: SystemStats) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (value: boolean) => void;
  setDarkMode: (value: boolean) => void;
  setIsLoading: (value: boolean) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  stats: null,
  isSidebarOpen: true,
  isDarkMode: false,
  isLoading: false,
  setStats: (stats) => set({ stats }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (value) => set({ isSidebarOpen: value }),
  setDarkMode: (value) => set({ isDarkMode: value }),
  setIsLoading: (value) => set({ isLoading: value }),
}));
