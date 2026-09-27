import { GUEST_COOKIE, GUEST_MAX_AGE_SECONDS } from "@/constants/storage";

export { GUEST_COOKIE };

export function setGuestCookie() {
  document.cookie = `${GUEST_COOKIE}=1; path=/; max-age=${GUEST_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function clearGuestCookie() {
  document.cookie = `${GUEST_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

export function hasGuestCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .some((part) => part.trim().startsWith(`${GUEST_COOKIE}=1`));
}
