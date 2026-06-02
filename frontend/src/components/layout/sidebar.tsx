"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSystemStore } from "@/stores/system-store";
import {
  LayoutDashboard,
  Smartphone,
  Phone,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/devices", label: "Devices", icon: Smartphone },
  { href: "/dashboard/calls", label: "Calls", icon: Phone },
  { href: "/dashboard/diagnostics", label: "Diagnostics", icon: Activity },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useSystemStore();
  const { logout } = useAuth();

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-card transition-all duration-300",
        isSidebarOpen ? "w-64" : "w-16",
      )}
    >
      <div className="flex h-14 items-center border-b px-4">
        {isSidebarOpen ? (
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="font-semibold">Call Reception</span>
          </div>
        ) : (
          <Activity className="mx-auto h-6 w-6 text-primary" />
        )}
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent hover:text-accent-foreground",
                !isSidebarOpen && "justify-center",
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {isSidebarOpen && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-2">
        <Button
          variant="ghost"
          size={isSidebarOpen ? "default" : "icon"}
          className={cn("w-full", !isSidebarOpen && "mx-auto")}
          onClick={logout}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {isSidebarOpen && <span className="ml-3">Logout</span>}
        </Button>
      </div>

      <button
        onClick={toggleSidebar}
        className="flex items-center justify-center border-t p-2 hover:bg-accent"
      >
        {isSidebarOpen ? (
          <ChevronLeft className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>
    </aside>
  );
}
