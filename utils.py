import os
import logging
import pyodbc
import json
import traceback
from flask import request
import base64

# Get database connection string
db_connection = os.getenv('DATABASE_URL', '')
logging.info(f"Database URL exists: {bool(db_connection)}")
if not db_connection:
    logging.error("DATABASE_URL environment variable is not set!")

def get_db_connection():
    """Get database connection with better error handling"""
    try:
        logging.info("Attempting database connection")
        if not db_connection:
            raise Exception("DATABASE_URL environment variable is not set")
        
        # Log connection string (without password)
        safe_connection = db_connection.replace(';', '\n').split('\n')
        logging.info("Connection details:")
        for part in safe_connection:
            if not part.lower().startswith('pwd=') and not part.lower().startswith('password='):
                logging.info(f"  {part}")
        
        conn = pyodbc.connect(db_connection)
        logging.info("Database connection successful")
        return conn
    except pyodbc.Error as e:
        logging.error(f"PyODBC Error: {str(e)}")
        logging.error(f"Connection string (sanitized): {';'.join([p for p in safe_connection if not p.lower().startswith('pwd=') and not p.lower().startswith('password=')])}")
        logging.error(traceback.format_exc())
        raise
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def log_audit(cursor, action_type, asset_tag, field_name, old_value, new_value, changed_by, notes=None):
    """Log an audit entry"""
    try:
        query = """
        INSERT INTO dbo.Inventory_Audit_Log 
        (action_type, asset_tag, field_name, old_value, new_value, changed_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (action_type, asset_tag, field_name, old_value, new_value, changed_by, notes))
    except Exception as e:
        logging.error(f"Error logging audit: {str(e)}")
        logging.error(traceback.format_exc())
        # Don't raise the exception - we don't want audit logging to break the main functionality
        
def get_user_name():
    """Get the current user's name from Azure AD claims"""
    try:
        principal = request.headers.get('X-MS-CLIENT-PRINCIPAL', '')
        if principal:
            principal_data = json.loads(base64.b64decode(principal).decode('utf-8'))
            for claim in principal_data.get('claims', []):
                if claim['typ'] in ['name', 'preferred_username', 'email']:
                    return claim['val']
        return 'Unknown User'
    except Exception as e:
        logging.error(f"Error getting user name: {str(e)}")
        return 'Unknown User'

def get_user_role(app_config):
    """Get user role from Azure AD claims"""
    try:
        # Log all headers for debugging
        logging.debug("All request headers:")
        for header, value in request.headers.items():
            logging.debug(f"{header}: {value}")

        # Get the principal header
        principal = request.headers.get('X-MS-CLIENT-PRINCIPAL', '')
        if not principal:
            logging.warning("No principal header found")
            return app_config['DEFAULT_ROLE']

        # Decode base64 principal
        principal_json = base64.b64decode(principal).decode('utf-8')
        principal_data = json.loads(principal_json)
        
        # Log the principal data for debugging
        logging.debug(f"Principal data: {principal_data}")
        
        # Extract roles from claims
        claims = principal_data.get('claims', [])
        roles = []
        for claim in claims:
            if claim['typ'].lower() in ['roles', 'role']:
                # Split in case multiple roles are in one claim
                claim_roles = claim['val'].split(',')
                roles.extend([r.strip() for r in claim_roles])
        
        logging.debug(f"Found roles: {roles}")
        
        # Create case-insensitive role mapping
        role_map = {k.lower(): k for k in app_config['ROLES'].keys()}
        
        # Map Azure AD roles to app roles
        for role in roles:
            role_lower = role.lower()
            if role_lower in role_map:
                actual_role = role_map[role_lower]
                logging.info(f"User assigned role: {actual_role}")
                return actual_role
        
        # Return default role if no matching role found
        logging.warning("No matching role found, using default")
        return app_config['DEFAULT_ROLE']
    except Exception as e:
        logging.error(f"Error getting user role: {str(e)}")
        logging.error(traceback.format_exc())
        return app_config['DEFAULT_ROLE']

def has_permission(required_permission, app_config):
    """Check if the current user has the required permission"""
    try:
        user_role = get_user_role(app_config)
        logging.debug(f"Checking permission '{required_permission}' for role '{user_role}'")
        
        if not user_role:
            logging.warning("No user role found")
            return False
        
        role_permissions = app_config['ROLE_PERMISSIONS'].get(user_role, [])
        logging.debug(f"Role permissions: {role_permissions}")
        
        has_perm = required_permission in role_permissions
        logging.debug(f"Has permission '{required_permission}': {has_perm}")
        
        return has_perm
    except Exception as e:
        logging.error(f"Error checking permissions: {str(e)}")
        logging.error(traceback.format_exc())
        return False
