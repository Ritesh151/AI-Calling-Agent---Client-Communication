"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { useAuthStore } from "@/stores/auth-store";
import { useAuth } from "@/hooks/use-auth";
import { useWebSocket } from "@/hooks/use-websocket";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();
  const { checkAuth } = useAuth();
  const [authReady, setAuthReady] = useState(false);

  useWebSocket(authReady && isAuthenticated);

  useEffect(() => {
    const token =
      localStorage.getItem("access_token") ||
      (document.cookie.includes("access_token") ? "cookie" : null);
    if (token) {
      checkAuth()
        .then((result) => {
          if (!result.data) {
            router.replace("/auth/login");
          }
        })
        .catch(() => router.replace("/auth/login"))
        .finally(() => setAuthReady(true));
    } else {
      useAuthStore.getState().setIsLoading(false);
      setAuthReady(true);
      router.replace("/auth/login");
    }
  }, [checkAuth, router]);

  useEffect(() => {
    if (authReady && !isLoading && !isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [authReady, isLoading, isAuthenticated, router]);

  if (!authReady || (isLoading && !isAuthenticated)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Header />
        <div className="shrink-0 px-6 py-3">
          <Breadcrumbs />
        </div>
        <main className="min-h-0 flex-1 overflow-y-auto px-6 py-4">{children}</main>
      </div>
    </div>
  );
}
