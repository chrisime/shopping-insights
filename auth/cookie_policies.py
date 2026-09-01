"""Named cookie groups shared across auth implementations."""

REQUIRED_REWE_COOKIE_NAMES = {"rstp"}
IMPORTANT_REWE_COOKIE_NAMES = {"_rdfa", "mtc"}
RECOMMENDED_REWE_WAF_COOKIE_NAMES = {"cf_clearance", "__cf_bm", "_cfuvid"}
KEYCLOAK_SSO_COOKIE_NAMES = {
    "KEYCLOAK_SESSION",
    "KEYCLOAK_IDENTITY",
    "KC_AUTH_SESSION_HASH",
}

REQUIRED_LIDL_COOKIE_NAMES = {"authToken"}
RECOMMENDED_LIDL_COOKIE_NAMES = {
    "ldi-customertoken",
    "ldi-user-context",
    "XSRF-TOKEN",
}
LIDL_IDENTITY_COOKIE_NAMES = {
    "customer-info",
    "tracking-info",
    "ldi-session-info",
    "LidlID",
}

# dm session cookies. The dm SSO session cookie (_SI_SID_*) carries a
# tenant-specific suffix, so required/recommended sets are resolved against
# the actual cookie names via these prefixes.
DM_REQUIRED_COOKIE_PREFIXES = ("_SI_SID_",)
DM_REQUIRED_COOKIE_NAMES = {"sessionid", "_sessionid"}
DM_RECOMMENDED_COOKIE_PREFIXES = ("_SI_DID_", "_SI_VID_", "_dyjsession", "_dyid_server")

