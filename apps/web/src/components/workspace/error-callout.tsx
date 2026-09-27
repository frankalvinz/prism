"use client";

import { SignInWithGitHub } from "@/components/auth/sign-in-with-github";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Routes } from "@/constants/routes";
import { useViewer } from "@/lib/api/auth-client";

export function ErrorCallout({
  message,
  errorCode,
  errorHint,
  showDemoAffordance,
  onDemo,
}: {
  message: string;
  errorCode?: string;
  errorHint?: string;
  showDemoAffordance: boolean;
  onDemo: () => void;
}) {
  const { viewer } = useViewer();
  const needsConnect =
    errorHint === "connect_github" || errorCode === "GITHUB_AUTH_EXPIRED";
  const reconnect = errorCode === "GITHUB_AUTH_EXPIRED";

  return (
    <Alert tone="danger" role="alert" className="rounded-xl px-4 py-3">
      <p className="font-medium">{message}</p>
      <div className="mt-3 flex flex-wrap items-start gap-3">
        {needsConnect ? (
          viewer?.oauth_enabled ? (
            <a
              href={Routes.githubLogin}
              className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:brightness-110"
            >
              {reconnect ? "Reconnect GitHub" : "Connect GitHub"}
            </a>
          ) : (
            <div className="max-w-xl">
              <SignInWithGitHub label={reconnect ? "Reconnect GitHub" : "Connect GitHub"} />
            </div>
          )
        ) : null}
        {showDemoAffordance ? (
          <Button type="button" variant="secondary" onClick={onDemo}>
            Run demo instead
          </Button>
        ) : null}
      </div>
    </Alert>
  );
}
