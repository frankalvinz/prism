"use client";

import { useEffect } from "react";

import { SignInWithGitHub } from "@/components/auth/sign-in-with-github";
import { LogoMark } from "@/components/brand/logo-mark";
import { SiteFooter } from "@/components/brand/site-footer";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LogoStage } from "@/components/welcome/logo-stage";
import { WELCOME_STEPS, WELCOME_TRUST } from "@/constants/content";
import { Routes } from "@/constants/routes";
import { useAuthErrorBanner } from "@/hooks/use-auth-error-banner";
import { useViewer } from "@/lib/api/auth-client";
import { setGuestCookie } from "@/lib/guest";

export function WelcomePage() {
  const { viewer, isLoading } = useViewer();
  const { authBanner } = useAuthErrorBanner();

  useEffect(() => {
    if (!isLoading && viewer?.authenticated) {
      window.location.replace(Routes.home);
    }
  }, [isLoading, viewer?.authenticated]);

  const continueAsGuest = () => {
    setGuestCookie();
    window.location.assign(Routes.home);
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6 sm:px-6 sm:py-8">
      <header className="mb-10 flex items-center justify-between gap-4">
        <LogoMark />
        <ThemeToggle />
      </header>

      {authBanner ? (
        <Alert tone="danger" className="mb-6">
          {authBanner}
        </Alert>
      ) : null}

      <section className="mb-14 grid gap-10 lg:grid-cols-[1fr_1.05fr] lg:items-center">
        <div className="animate-fade-up space-y-6">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-primary">
            GitHub pull request analyzer
          </p>
          <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Understand every pull request before you review it.
          </h1>
          <p className="max-w-lg text-base leading-relaxed text-muted sm:text-lg">
            PRISM turns PR metadata and diffs into a clear change report — risks, tests, complexity,
            and review questions — without requiring an AI provider.
          </p>

          <div className="flex flex-col items-stretch gap-3 pt-2 sm:items-start">
            <SignInWithGitHub size="lg" />
            <Button
              type="button"
              variant="secondary"
              className="w-full sm:w-auto"
              onClick={continueAsGuest}
            >
              Continue without signing in
            </Button>
            <p className="text-xs text-muted">
              Public PRs and the demo work without an account.
            </p>
          </div>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: "120ms" }}>
          <LogoStage />
        </div>
      </section>

      <section className="mb-14">
        <h2 className="mb-6 text-xl font-semibold text-foreground">How it works</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {WELCOME_STEPS.map((step, index) => (
            <Card
              key={step.title}
              as="article"
              className="animate-fade-up p-5"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="mb-3 font-mono text-xs text-primary">
                {String(index + 1).padStart(2, "0")}
              </div>
              <h3 className="mb-2 text-base font-medium text-foreground">{step.title}</h3>
              <p className="text-sm leading-relaxed text-muted">{step.body}</p>
            </Card>
          ))}
        </div>
      </section>

      <Card as="section" className="mb-10 rounded-2xl p-6 sm:p-8">
        <h2 className="mb-2 text-xl font-semibold text-foreground">Why sign in with GitHub?</h2>
        <p className="mb-5 max-w-2xl text-sm text-muted">
          Sign-in is optional for public repositories. Connect when you need private access or a
          personal open-PR feed.
        </p>
        <ul className="space-y-3">
          {WELCOME_TRUST.map((item) => (
            <li key={item} className="flex gap-3 text-sm text-foreground">
              <span
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                aria-hidden
              />
              <span className="leading-relaxed text-muted">{item}</span>
            </li>
          ))}
        </ul>
      </Card>

      <SiteFooter />
    </div>
  );
}
