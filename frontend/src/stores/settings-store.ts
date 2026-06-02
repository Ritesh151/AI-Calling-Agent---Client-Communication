import { create } from "zustand";
import type { Setting } from "@/types";

interface SettingsState {
  settings: Setting[];
  settingsMap: Record<string, string>;
  isLoading: boolean;
  setSettings: (settings: Setting[]) => void;
  setIsLoading: (value: boolean) => void;
  updateSetting: (id: number, data: Partial<Setting>) => void;
  getValue: (key: string, defaultValue?: string) => string;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: [],
  settingsMap: {},
  isLoading: false,
  setSettings: (settings) =>
    set({
      settings,
      settingsMap: settings.reduce(
        (acc, s) => ({ ...acc, [s.key]: s.value }),
        {} as Record<string, string>,
      ),
    }),
  setIsLoading: (value) => set({ isLoading: value }),
  updateSetting: (id, data) =>
    set((state) => {
      const newSettings = state.settings.map((s) =>
        s.id === id ? { ...s, ...data } : s,
      );
      return {
        settings: newSettings,
        settingsMap: newSettings.reduce(
          (acc, s) => ({ ...acc, [s.key]: s.value }),
          {} as Record<string, string>,
        ),
      };
    }),
  getValue: (key, defaultValue = "") => {
    return get().settingsMap[key] || defaultValue;
  },
}));
