import os

# Azure AD settings
CLIENT_ID = "31eb29e9-2e74-4fdc-8515-d774832276f3"
TENANT_ID = "ae128315-4515-4382-89e8-094e98d313bc"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"  
SCOPE = ["User.Read"]  # Add more scopes as needed
SESSION_TYPE = "filesystem"

# The absolute URL must match your Azure AD app registration redirect URI
REDIRECT_URI = "https://inventory-app-sean.azurewebsites.net/getAToken"

# Database settings
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///inventory.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
