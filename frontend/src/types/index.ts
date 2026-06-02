export interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: number;
  user_id: number | null;
  device_name: string;
  android_id: string | null;
  serial_number: string | null;
  manufacturer: string | null;
  model: string | null;
  android_version: string | null;
  status: string;
  is_connected: boolean;
  last_seen: string | null;
  battery_level: number | null;
  charging: boolean | null;
  screen_state: string | null;
  created_at: string;
  updated_at: string;
}

export interface CallSession {
  id: number;
  device_id: number;
  caller_name: string | null;
  caller_number: string | null;
  call_status: string;
  language: string | null;
  start_time: string | null;
  end_time: string | null;
  duration: number | null;
  recording_path: string | null;
  transcription: string | null;
  incoming_detected_at?: string | null;
  answered_at?: string | null;
  caller_type?: string | null;
  raw_call_data?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  conversation_id: number;
  call_session_id: number;
  speaker: "AI" | "USER" | string;
  message_type: string;
  content: string;
  language: string | null;
  question_index: number | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: number;
  call_session_id: number;
  language: string | null;
  status: string;
  current_question_index: number;
  total_questions: number;
  completion_percentage: number;
  transcript: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

export interface Setting {
  id: number;
  key: string;
  value: string;
  description: string | null;
  category: string | null;
  updated_at: string;
}

export interface SystemLog {
  id: number;
  level: string;
  module: string;
  message: string;
  metadata_json: string | null;
  logged_at: string;
}

export interface SystemStats {
  total_devices: number;
  connected_devices: number;
  total_calls: number;
  active_calls: number;
  total_users: number;
  total_logs: number;
  server_time: string;
  python_version: string;
  platform: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ApiError {
  success: false;
  message: string;
  error_code: string;
  details: Record<string, unknown> | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}
