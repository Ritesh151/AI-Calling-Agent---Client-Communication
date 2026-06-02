import apiClient from "./api";
import type { ApiResponse, SystemStats } from "@/types";

export interface SystemDiagnostics {
  database: { status: string; message: string };
  redis: { status: string; message: string };
  adb: Record<string, unknown>;
  devices: { connected: number; adb_found: number };
  workers: Record<string, { running: boolean; detail: string }>;
  websocket: { active_connections: number };
  call_detection: { poll_interval_seconds: number };
  auto_answer: { enabled: boolean; device_ready: boolean; can_answer: boolean };
  ai: { provider: string; configured: boolean };
}

export const systemService = {
  async getStats(): Promise<ApiResponse<SystemStats>> {
    const response = await apiClient.get<ApiResponse<SystemStats>>("/system/stats");
    return response.data;
  },

  async getDiagnostics(): Promise<ApiResponse<SystemDiagnostics>> {
    const response = await apiClient.get<ApiResponse<SystemDiagnostics>>("/system/diagnostics");
    return response.data;
  },
};
