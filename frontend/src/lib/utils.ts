import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return "N/A";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "connected":
    case "active":
    case "completed":
      return "text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400";
    case "disconnected":
    case "missed":
    case "failed":
      return "text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400";
    case "pending":
    case "busy":
      return "text-yellow-600 bg-yellow-50 dark:bg-yellow-950 dark:text-yellow-400";
    default:
      return "text-gray-600 bg-gray-50 dark:bg-gray-950 dark:text-gray-400";
  }
}

export function getStatusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
