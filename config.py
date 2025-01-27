import os

# Azure AD Configuration
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
TENANT_ID = os.environ.get('TENANT_ID')
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
REDIRECT_URI = os.environ.get('AZURE_REDIRECT_URI', 'https://inventory-app-sean.azurewebsites.net/getAToken')
REDIRECT_PATH = '/getAToken'  # This matches the path in REDIRECT_URI
SCOPE = ['User.Read']

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
