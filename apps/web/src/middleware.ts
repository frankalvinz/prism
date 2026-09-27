import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { Routes } from "@/constants/routes";
import { GUEST_COOKIE, SESSION_COOKIE } from "@/constants/storage";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(SESSION_COOKIE)?.value);
  const hasGuest = request.cookies.get(GUEST_COOKIE)?.value === "1";
  const isWelcome =
    pathname === Routes.welcome || pathname.startsWith(`${Routes.welcome}/`);

  if (isWelcome && hasSession) {
    return NextResponse.redirect(new URL(Routes.home, request.url));
  }

  if (pathname === Routes.home && !hasSession && !hasGuest) {
    return NextResponse.redirect(new URL(Routes.welcome, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/welcome", "/welcome/:path*"],
};
