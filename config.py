import os
from datetime import timedelta

# Azure AD settings
CLIENT_ID = os.getenv('CLIENT_ID', "31eb29e9-2e74-4fdc-8515-d774832276f3")
CLIENT_SECRET = os.getenv('CLIENT_SECRET', "rJE8Q~Zqviy1Fg-tSKBMJ-eeX13ZY5ahSxftYa28")
TENANT_ID = os.getenv('TENANT_ID', "ae128315-4515-4382-89e8-094e98d313bc")

# Azure AD URLs
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/callback"  # This must match your Azure AD redirect URI

# App URLs
if os.getenv('WEBSITE_HOSTNAME'):
    # Running in Azure
    BASE_URL = f"https://{os.getenv('WEBSITE_HOSTNAME')}"
else:
    # Running locally
    BASE_URL = "http://localhost:5000"

REDIRECT_URI = f"{BASE_URL}{REDIRECT_PATH}"

# OAuth settings
SCOPE = [
    "User.Read",
    "User.ReadBasic.All"
]

# Session settings
SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))  # For session encryption

# Enable debug logging for MSAL
LOGGING_LEVEL = 'DEBUG'
