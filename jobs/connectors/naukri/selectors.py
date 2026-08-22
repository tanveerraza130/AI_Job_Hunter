"""
Playwright selectors used by the Naukri connector.

Only login/session related selectors belong here.
Job extraction is performed via the Naukri Search API.
"""

from __future__ import annotations

# =============================================================================
# Generic
# =============================================================================

BODY = "body"

# =============================================================================
# Authentication
# =============================================================================

LOGIN_BUTTON = 'a[id="login_Layer"]'

EMAIL_INPUT = 'input[placeholder*="Email"]'
PASSWORD_INPUT = 'input[type="password"]'

LOGIN_SUBMIT = 'button[type="submit"]'

PROFILE_ICON = ".nI-gNb-drawer"
PROFILE_MENU = ".nI-gNb-menuItems"

# =============================================================================
# Session / State
# =============================================================================

COOKIE_ACCEPT = 'button[id*="accept"]'
CLOSE_POPUP = 'button[aria-label="Close"]'