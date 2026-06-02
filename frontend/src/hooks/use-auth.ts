"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth-store";
import type { LoginRequest, RegisterRequest, User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading, setUser, setIsLoading, logout: storeLogout } = useAuthStore();

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      setIsLoading(true);
      try {
        const response = await authService.getMe();
        const next = response?.data ?? null;
        setUser(next);
        return next;
      } catch (error) {
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 401) {
          setUser(null);
        }
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    retry: (failureCount, error: unknown) => {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 401 || status === 403) return false;
      return failureCount < 1;
    },
    enabled: false,
  });

  const loginMutation = useMutation({
    mutationFn: (data: LoginRequest) => authService.login(data),
    onSuccess: async (response) => {
      const loginData = response?.data as unknown as Record<string, unknown> | undefined;
      const userFromLogin: User | null = (loginData?.user as User) ?? null;
      if (userFromLogin) {
        setUser(userFromLogin);
        queryClient.setQueryData(["auth", "me"], userFromLogin);
      } else {
        try {
          const me = await authService.getMe();
          const next = me?.data ?? null;
          setUser(next);
          queryClient.setQueryData(["auth", "me"], next);
        } catch (error) {
          const status = (error as { response?: { status?: number } })?.response?.status;
          if (status !== 401) {
            console.warn("Post-login /auth/me failed; dashboard will retry.", error);
          }
        }
      }
      router.push("/dashboard");
    },
  });

  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: () => {
      router.push("/auth/login");
    },
  });

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      storeLogout();
      queryClient.clear();
      router.push("/auth/login");
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    register: registerMutation.mutate,
    logout,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    checkAuth: meQuery.refetch,
  };
}
