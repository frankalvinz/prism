import type { PullRequestFilter } from "@prism/shared";

export const ApiRoutes = {
  analyze: "/api/v1/analyze",
  authMe: "/api/v1/auth/me",
  authLogout: "/api/v1/auth/logout",
  myPullRequests: (filter: PullRequestFilter) =>
    `/api/v1/me/pull-requests?filter=${encodeURIComponent(filter)}`,
} as const;
