"use client";

import { useEffect, useState } from "react";

import { authErrorMessage } from "@/lib/api/analyze-client";

export function useAuthErrorBanner() {
  const [authBanner, setAuthBanner] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const authError = params.get("auth_error");
    if (authError) {
      setAuthBanner(authErrorMessage(authError));
      const next = new URL(window.location.href);
      next.searchParams.delete("auth_error");
      window.history.replaceState({}, "", next.pathname + next.search);
    }
  }, []);

  return { authBanner, setAuthBanner };
}
