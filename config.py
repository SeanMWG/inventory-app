import os

# Role definitions
ROLES = {
    'admin': 'Admin',      # Can perform all operations
    'editor': 'Editor',    # Can add and edit items
    'viewer': 'Viewer'     # Can only view items
}

# Role permissions
ROLE_PERMISSIONS = {
    'admin': ['view', 'add', 'edit', 'delete'],
    'editor': ['view', 'add', 'edit'],
    'viewer': ['view']
}

# Default role for users if no role is assigned
DEFAULT_ROLE = 'viewer'

# Database URL (will be provided by environment variable)
DATABASE_URL = os.getenv('DATABASE_URL')
