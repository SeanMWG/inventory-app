import os

# Azure AD Configuration
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
REDIRECT_URI = os.getenv('AZURE_REDIRECT_URI', 'https://inventory-app-sean.azurewebsites.net/getAToken')
REDIRECT_PATH = '/getAToken'  # This matches the path in REDIRECT_URI
SCOPE = ['User.Read']

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
