import type { AnalysisReport } from "@prism/shared";

import { ApiRoutes } from "@/constants/api-routes";
import { AnalyzeApiError, apiFetch } from "@/lib/api/http";

export { AnalyzeApiError };

export async function analyzePullRequest(input: {
  url?: string;
  demo?: boolean;
}): Promise<AnalysisReport> {
  return apiFetch<AnalysisReport>(ApiRoutes.analyze, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

const GENERIC_MESSAGES: Record<string, string> = {
  INVALID_URL: "That doesn’t look like a valid GitHub pull request URL.",
  GITHUB_NOT_FOUND: "Repository or pull request was not found (it may be private).",
  GITHUB_RATE_LIMITED: "GitHub API rate limit reached. Try the demo or retry later.",
  GITHUB_API_ERROR: "GitHub API returned an error.",
  GITHUB_AUTH_EXPIRED: "GitHub session expired. Please reconnect GitHub.",
  PR_TOO_LARGE: "This PR exceeds the current analysis limit.",
  ANALYSIS_FAILED: "Analysis failed unexpectedly.",
  UNSUPPORTED_CONTENT: "Unsupported content for analysis.",
};

const CONNECTIVITY_MESSAGE =
  "Could not reach GitHub (network or SSL). Try Demo PR, or check connectivity.";

function looksLikeConnectivityFailure(message: string, details: Record<string, unknown>): boolean {
  const reason = typeof details.reason === "string" ? details.reason.toLowerCase() : "";
  const combined = `${message} ${reason}`.toLowerCase();
  return (
    message === "Failed to reach GitHub API." ||
    combined.includes("connecterror") ||
    combined.includes("connect error") ||
    combined.includes("connection") ||
    combined.includes("ssl") ||
    combined.includes("certificate") ||
    combined.includes("timed out") ||
    combined.includes("timeout") ||
    combined.includes("name or service not known") ||
    combined.includes("getaddrinfo")
  );
}

export function isConnectivityError(message?: string, code?: string): boolean {
  if (code !== "GITHUB_API_ERROR" || !message) return false;
  return (
    message === CONNECTIVITY_MESSAGE ||
    message.toLowerCase().includes("could not reach github") ||
    message === "Failed to reach GitHub API."
  );
}

export function needsConnectGitHub(error: AnalyzeApiError | null | undefined): boolean {
  if (!error) return false;
  return error.code === "GITHUB_NOT_FOUND" && error.details?.hint === "connect_github";
}

function formatApiErrorMessage(error: AnalyzeApiError): string {
  const { code, message, details } = error;

  if (code === "GITHUB_AUTH_EXPIRED") {
    return GENERIC_MESSAGES.GITHUB_AUTH_EXPIRED;
  }

  if (code === "GITHUB_API_ERROR") {
    if (looksLikeConnectivityFailure(message, details)) {
      return CONNECTIVITY_MESSAGE;
    }
    if (message && message !== GENERIC_MESSAGES.GITHUB_API_ERROR) {
      return message;
    }
    const status = details.status;
    const githubMessage = details.github_message;
    if (typeof status === "number" && typeof githubMessage === "string" && githubMessage) {
      return `GitHub API returned ${status}: ${githubMessage}`;
    }
    if (typeof githubMessage === "string" && githubMessage) {
      return `GitHub API returned an error: ${githubMessage}`;
    }
    if (typeof status === "number") {
      return `GitHub API returned status ${status}.`;
    }
  }

  if (message && message !== GENERIC_MESSAGES[code]) {
    return message;
  }

  return GENERIC_MESSAGES[code] || message || "Unexpected analysis failure.";
}

export function mapErrorToState(error: unknown): {
  code: string;
  message: string;
  details: Record<string, unknown>;
} {
  if (error instanceof AnalyzeApiError) {
    return {
      code: error.code,
      message: formatApiErrorMessage(error),
      details: error.details,
    };
  }
  if (error instanceof Error) {
    return { code: "ANALYSIS_FAILED", message: error.message, details: {} };
  }
  return {
    code: "ANALYSIS_FAILED",
    message: "Unexpected analysis failure.",
    details: {},
  };
}

export function authErrorMessage(code: string | null): string | null {
  if (!code) return null;
  const messages: Record<string, string> = {
    oauth_disabled: "GitHub OAuth is not configured on this server.",
    state_mismatch: "GitHub sign-in failed (security check). Please try again.",
    missing_code: "GitHub sign-in was cancelled or incomplete.",
    exchange_failed: "Could not complete GitHub sign-in. Please try again.",
    session_failed: "Could not create a secure session. Check SESSION_SECRET.",
    access_denied: "GitHub access was denied.",
  };
  return messages[code] || `GitHub sign-in failed (${code}).`;
}
