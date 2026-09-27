"use client";

import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { SiteFooter } from "@/components/brand/site-footer";
import { AnalysisDashboard } from "@/components/report/analysis-dashboard";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AnalysisProgress } from "@/components/workspace/analysis-progress";
import { AnalyzeBar } from "@/components/workspace/analyze-bar";
import { AppHeader } from "@/components/workspace/app-header";
import { ErrorCallout } from "@/components/workspace/error-callout";
import { MyPullRequestsPanel } from "@/components/workspace/my-pull-requests-panel";
import { QuickStartCards } from "@/components/workspace/quick-start-cards";
import { Routes } from "@/constants/routes";
import { useAuthErrorBanner } from "@/hooks/use-auth-error-banner";
import { useViewer } from "@/lib/api/auth-client";
import {
  analyzePullRequest,
  isConnectivityError,
  mapErrorToState,
} from "@/lib/api/analyze-client";
import { hasGuestCookie } from "@/lib/guest";
import type { UiPhase } from "@/lib/analysis/phases";

export function AnalyzerApp() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<UiPhase>("idle");
  const [errorCode, setErrorCode] = useState<string | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [errorHint, setErrorHint] = useState<string | undefined>();

  const { viewer, isLoading: viewerLoading, refetch: refetchViewer } = useViewer();
  const { authBanner } = useAuthErrorBanner();
  const phaseTimersRef = useRef<number[]>([]);
  const runIdRef = useRef(0);

  const clearPhaseTimers = () => {
    for (const id of phaseTimersRef.current) {
      window.clearTimeout(id);
    }
    phaseTimersRef.current = [];
  };

  useEffect(() => () => clearPhaseTimers(), []);

  useEffect(() => {
    if (viewerLoading) return;
    if (!viewer?.authenticated && !hasGuestCookie()) {
      router.replace(Routes.welcome);
    }
  }, [viewer, viewerLoading, router]);

  useEffect(() => {
    if (authBanner) {
      void refetchViewer();
    }
  }, [authBanner, refetchViewer]);

  const mutation = useMutation({
    mutationFn: analyzePullRequest,
    onMutate: (vars) => {
      clearPhaseTimers();
      const runId = ++runIdRef.current;

      setErrorCode(undefined);
      setErrorMessage(undefined);
      setErrorHint(undefined);

      if (vars.demo) {
        setPhase("analyzing");
        return;
      }

      setPhase("parsing");

      const schedule = (delayMs: number, next: UiPhase) => {
        const id = window.setTimeout(() => {
          if (runIdRef.current !== runId) return;
          setPhase((current) =>
            current === "completed" || current === "error" ? current : next,
          );
        }, delayMs);
        phaseTimersRef.current.push(id);
      };

      schedule(200, "fetching");
      schedule(700, "analyzing");
    },
    onSuccess: () => {
      clearPhaseTimers();
      setPhase("completed");
    },
    onError: (err) => {
      clearPhaseTimers();
      const mapped = mapErrorToState(err);
      setErrorCode(mapped.code);
      setErrorMessage(mapped.message);
      setErrorHint(
        typeof mapped.details.hint === "string" ? mapped.details.hint : undefined,
      );
      setPhase("error");
      if (mapped.code === "GITHUB_AUTH_EXPIRED") {
        void refetchViewer();
      }
    },
  });

  const showDemoAffordance =
    phase === "error" &&
    (errorCode === "GITHUB_RATE_LIMITED" ||
      (errorCode === "GITHUB_API_ERROR" && isConnectivityError(errorMessage, errorCode)));

  const runAnalyze = (nextUrl?: string) => {
    const target = (nextUrl ?? url).trim();
    if (!target) return;
    if (nextUrl) setUrl(nextUrl);
    mutation.mutate({ url: target });
  };

  const resetToIdle = () => {
    clearPhaseTimers();
    runIdRef.current += 1;
    mutation.reset();
    setPhase("idle");
    setErrorCode(undefined);
    setErrorMessage(undefined);
    setErrorHint(undefined);
  };

  const isBusy = mutation.isPending;
  const showIdleWorkspace = phase === "idle" || (phase === "error" && !mutation.data);
  const showReport = phase === "completed" && Boolean(mutation.data);

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 sm:px-6">
      <AppHeader />

      <div className="mb-6 space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Analyze a pull request
        </h1>
        <p className="max-w-2xl text-sm text-muted">
          Paste a GitHub PR URL, pick one of your open PRs, or try the demo. Deterministic analysis —
          no API key required.
        </p>
      </div>

      {authBanner ? (
        <Alert tone="danger" className="mb-6">
          {authBanner}
        </Alert>
      ) : null}

      <div className="mb-6">
        <AnalyzeBar
          url={url}
          onUrlChange={setUrl}
          onAnalyze={() => runAnalyze()}
          onDemo={() => mutation.mutate({ demo: true })}
          isPending={isBusy}
          compact={showReport}
        />
      </div>

      <div className="mb-6 space-y-4">
        <AnalysisProgress phase={phase} />
        {phase === "error" && errorMessage ? (
          <ErrorCallout
            message={errorMessage}
            errorCode={errorCode}
            errorHint={errorHint}
            showDemoAffordance={showDemoAffordance}
            onDemo={() => mutation.mutate({ demo: true })}
          />
        ) : null}
      </div>

      {showReport && mutation.data ? (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button type="button" variant="secondary" onClick={resetToIdle}>
              New analysis
            </Button>
          </div>
          <AnalysisDashboard report={mutation.data} />
        </div>
      ) : null}

      {showIdleWorkspace && !showReport ? (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
          <MyPullRequestsPanel
            isPending={isBusy}
            onAnalyze={(htmlUrl) => runAnalyze(htmlUrl)}
          />
          <QuickStartCards onDemo={() => mutation.mutate({ demo: true })} />
        </div>
      ) : null}

      <SiteFooter />
    </div>
  );
}
