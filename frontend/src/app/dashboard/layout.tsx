"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
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
  const authCheckStartedRef = useRef(false);

  useWebSocket(authReady && isAuthenticated);

  useEffect(() => {
    if (authCheckStartedRef.current) return;
    authCheckStartedRef.current = true;

    const token = localStorage.getItem("access_token");
    if (!token) {
      useAuthStore.getState().setIsLoading(false);
      setAuthReady(true);
      return;
    }
    checkAuth().finally(() => setAuthReady(true));
  }, [checkAuth]);

  useEffect(() => {
    if (authReady && !isLoading && !isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [authReady, isLoading, isAuthenticated, router]);

  if (!authReady) {

    

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
