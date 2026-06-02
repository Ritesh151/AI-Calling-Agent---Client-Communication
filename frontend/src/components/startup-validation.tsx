"use client";

import { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

export function StartupValidation() {
  const { checkAuth } = useAuth();
  const { connectionStatus, backendHealth, updateBackendHealth } = useWebSocket();
  const router = useRouter();
  const [isValidating, setIsValidating] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    const validateStartup = async () => {
      try {
        // Check authentication
        const token =
          localStorage.getItem("access_token") ||
          document.cookie.includes("access_token");
        
        if (token) {
          await checkAuth();
        } else {
          setValidationError("No authentication token found");
          router.push("/auth/login");
          return;
        }

        // Check backend health
        const backendResponse = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/health`
        );
        const backendData = await backendResponse.json();
        
        if (!backendResponse.ok) {
          setValidationError(`Backend unhealthy: ${backendData.message}`);
          updateBackendHealth(false);
          return;
        }
        
        updateBackendHealth(true);

        // Additional WebSocket-specific checks could go here
        // The WebSocket connection will be established by the useWebSocket hook

        setIsValidating(false);
      } catch (error) {
        setValidationError(
          `Startup validation failed: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
        setIsValidating(false);
      }
    };

    validateStartup();
  }, [checkAuth, router, updateBackendHealth]);

  if (isValidating) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background/50 backdrop-blur z-50">
        <div className="text-center space-y-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <h3 className="text-lg font-bold">Validating System...</h3>
          <p className="text-sm text-muted-foreground">
            Checking authentication, backend connectivity, and WebSocket availability
          </p>
        </div>
      </div>
    );
  }

  if (validationError) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background/90 backdrop-blur z-50">
        <div className="w-full max-w-md space-y-4">
          <Alert variant="destructive">
            <AlertTitle>System Validation Failed</AlertTitle>
            <AlertDescription>{validationError}</AlertDescription>
          </Alert>
          <Button onClick={() => window.location.reload()} className="w-full">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Validation
          </Button>
        </div>
      </div>
    );
  }

  return null; // Validation passed, render children
}