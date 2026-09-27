"use client";

import { useQuery } from "@tanstack/react-query";
import type { OpenPullRequestsResponse, PullRequestFilter } from "@prism/shared";

import { ApiRoutes } from "@/constants/api-routes";
import { useViewer } from "@/lib/api/auth-client";
import { apiFetch } from "@/lib/api/http";

export function useMyPullRequests(filter: PullRequestFilter) {
  const { viewer } = useViewer();
  return useQuery({
    queryKey: ["my-pull-requests", filter, viewer?.login ?? null],
    queryFn: () => apiFetch<OpenPullRequestsResponse>(ApiRoutes.myPullRequests(filter)),
    enabled: Boolean(viewer?.authenticated),
    staleTime: 60_000,
  });
}
