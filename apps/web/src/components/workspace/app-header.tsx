"use client";

import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { useRouter } from "next/navigation";

import { SignInWithGitHub } from "@/components/auth/sign-in-with-github";
import { LogoMark } from "@/components/brand/logo-mark";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { Routes } from "@/constants/routes";
import { useViewer } from "@/lib/api/auth-client";
import { hasGuestCookie } from "@/lib/guest";

export function AppHeader() {
  const router = useRouter();
  const { viewer, isLoading, logout, isLoggingOut } = useViewer();

  const onDisconnect = async () => {
    await logout();
    if (hasGuestCookie()) return;
    router.push(Routes.welcome);
  };

  return (
    <header className="sticky top-0 z-40 -mx-4 mb-8 border-b border-border bg-canvas/80 px-4 backdrop-blur-md sm:-mx-6 sm:px-6">
      <div className="flex h-14 items-center justify-between gap-3">
        <LogoMark />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {isLoading ? (
            <div className="h-9 w-24 animate-pulse rounded-md bg-panel-2" />
          ) : viewer?.authenticated && viewer.login ? (
            <Menu as="div" className="relative">
              <MenuButton className="inline-flex items-center gap-2 rounded-md border border-border bg-panel px-2 py-1.5 text-sm text-foreground hover:border-primary">
                {viewer.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={viewer.avatar_url}
                    alt=""
                    width={24}
                    height={24}
                    className="h-6 w-6 rounded-full"
                  />
                ) : (
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-panel-2 font-mono text-[10px]">
                    {viewer.login.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <span className="hidden font-mono text-xs sm:inline">@{viewer.login}</span>
              </MenuButton>
              <MenuItems className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg border border-border bg-panel p-1 shadow-lg outline-none">
                <div className="px-3 py-2 text-xs text-muted">
                  Signed in as{" "}
                  <span className="font-mono text-foreground">@{viewer.login}</span>
                </div>
                <MenuItem>
                  <button
                    type="button"
                    disabled={isLoggingOut}
                    onClick={() => void onDisconnect()}
                    className="w-full rounded-md px-3 py-2 text-left text-sm text-danger data-focus:bg-panel-2"
                  >
                    Disconnect
                  </button>
                </MenuItem>
              </MenuItems>
            </Menu>
          ) : viewer?.oauth_enabled ? (
            <SignInWithGitHub label="Sign in" className="!px-3 !py-1.5 !text-sm" />
          ) : (
            <Button type="button" variant="secondary" disabled className="!px-3 !py-1.5 !text-sm">
              Sign in
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
