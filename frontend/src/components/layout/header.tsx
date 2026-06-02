"use client";

import { usePathname } from "next/navigation";
import { useSystemStore } from "@/stores/system-store";
import { useAuthStore } from "@/stores/auth-store";
import { Moon, Sun, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";

const routeTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/devices": "Devices",
  "/dashboard/calls": "Calls",
  "/dashboard/calls/live": "Live Calls",
  "/dashboard/settings": "Settings",
  "/dashboard/diagnostics": "Diagnostics",
  "/dashboard/profile": "Profile",
};

export function Header() {
  const pathname = usePathname();
  const { isDarkMode, setDarkMode } = useSystemStore();
  const { user } = useAuthStore();

  const title = routeTitles[pathname] || "AI Call Reception";

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setDarkMode(!isDarkMode)}
        >
          {isDarkMode ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>

        <div className="flex items-center gap-2">
          <div className="text-right">
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-muted-foreground">{user?.role}</p>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
            {user?.username?.charAt(0).toUpperCase()}
          </div>
        </div>
      </div>
    </header>
  );
}
