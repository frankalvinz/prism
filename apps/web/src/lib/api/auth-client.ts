"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Viewer } from "@prism/shared";

import { ApiRoutes } from "@/constants/api-routes";
import { apiFetch } from "@/lib/api/http";

const ANONYMOUS_VIEWER: Viewer = {
  oauth_enabled: false,
  authenticated: false,
  login: null,
  avatar_url: null,
};

async function fetchViewer(): Promise<Viewer> {
  return apiFetch<Viewer>(ApiRoutes.authMe, undefined, {
    fallbackOnError: ANONYMOUS_VIEWER,
  });
}

async function logoutRequest(): Promise<void> {
  await apiFetch<{ ok: boolean }>(ApiRoutes.authLogout, { method: "POST" });
}

export function useViewer() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["viewer"],
    queryFn: fetchViewer,
    staleTime: 60_000,
  });

  const logout = useMutation({
    mutationFn: logoutRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["viewer"] });
    },
  });

  return {
    viewer: query.data,
    isLoading: query.isLoading,
    refetch: query.refetch,
    logout: logout.mutateAsync,
    isLoggingOut: logout.isPending,
  };
}
