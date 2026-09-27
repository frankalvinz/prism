"""Central path, cookie, and TTL constants for the PRISM API."""

API_PREFIX = "/api/v1"
AUTH_PREFIX = f"{API_PREFIX}/auth"
ME_PREFIX = f"{API_PREFIX}/me"
OAUTH_CALLBACK_PATH = f"{AUTH_PREFIX}/github/callback"

WEB_HOME_PATH = "/"
WEB_WELCOME_PATH = "/welcome"

SESSION_COOKIE = "prism_session"
STATE_COOKIE = "prism_oauth_state"
STATE_TTL_SECONDS = 600

OPEN_PRS_CACHE_TTL = 60
