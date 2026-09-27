export const Routes = {
  home: "/",
  welcome: "/welcome",
  githubLogin: "/api/v1/auth/github/login",
  assets_logoLong: "/assets/logo/logo-long.png",
  assets_logoShort: "/assets/logo/logo-short.png",
} as const;

export type AppRoute = (typeof Routes)[keyof typeof Routes];
