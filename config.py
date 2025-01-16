import os

# Azure AD settings
CLIENT_ID = "31eb29e9-2e74-4fdc-8515-d774832276f3"  # Replace with your actual client ID
CLIENT_SECRET = "7955b14a-c78c-4a3b-aaa4-1b8cb01337d9"  # Replace with your actual client secret
TENANT_ID = "ae128315-4515-4382-89e8-094e98d313bc"  # Replace with your actual tenant ID

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
SECRET_KEY = os.urandom(32)  # For session encryption
