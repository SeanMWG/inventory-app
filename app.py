from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import os
from flask_cors import CORS
from datetime import datetime
import logging
import sys
import pyodbc
from functools import wraps
import json
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
app.config.from_object('config')

# Configure CORS to work with credentials
CORS(app, supports_credentials=True)

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

def get_user_role():
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
            return app.config['DEFAULT_ROLE']

        # Decode base64 principal
        import base64
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
        role_map = {k.lower(): k for k in app.config['ROLES'].keys()}
        
        # Map Azure AD roles to app roles
        for role in roles:
            role_lower = role.lower()
            if role_lower in role_map:
                actual_role = role_map[role_lower]
                logging.info(f"User assigned role: {actual_role}")
                return actual_role
        
        # Return default role if no matching role found
        logging.warning("No matching role found, using default")
        return app.config['DEFAULT_ROLE']
    except Exception as e:
        logging.error(f"Error getting user role: {str(e)}")
        logging.error(traceback.format_exc())
        return app.config['DEFAULT_ROLE']

def has_permission(required_permission):
    """Check if the current user has the required permission"""
    try:
        user_role = get_user_role()
        logging.debug(f"Checking permission '{required_permission}' for role '{user_role}'")
        
        if not user_role:
            logging.warning("No user role found")
            return False
        
        role_permissions = app.config['ROLE_PERMISSIONS'].get(user_role, [])
        logging.debug(f"Role permissions: {role_permissions}")
        
        has_perm = required_permission in role_permissions
        logging.debug(f"Has permission '{required_permission}': {has_perm}")
        
        return has_perm
    except Exception as e:
        logging.error(f"Error checking permissions: {str(e)}")
        logging.error(traceback.format_exc())
        return False

@app.route('/api/user/role')
def get_user_role_api():
    """API endpoint to get the current user's role"""
    try:
        role = get_user_role()
        permissions = app.config['ROLE_PERMISSIONS'].get(role, [])
        logging.info(f"User role API - Role: {role}, Permissions: {permissions}")
        return jsonify({
            'role': role,
            'permissions': permissions
        })
    except Exception as e:
        logging.error(f"Error in role API: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def role_required(permission):
    """Decorator to require specific permission for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not has_permission(permission):
                    logging.warning(f"Permission denied: {permission}")
                    return jsonify({
                        'error': 'Permission denied',
                        'required_permission': permission
                    }), 403
                return f(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in role_required decorator: {str(e)}")
                logging.error(traceback.format_exc())
                return jsonify({'error': 'Internal server error'}), 500
        return decorated_function
    return decorator

@app.route('/api/hardware', methods=['GET'])
@role_required('view')
def get_hardware():
    """Get hardware items with better error handling"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 35
        
        # Get filter parameters
        filters = {
            'site_name': request.args.get('site_name'),
            'room_number': request.args.get('room_number'),
            'room_name': request.args.get('room_name'),
            'asset_tag': request.args.get('asset_tag'),
            'asset_type': request.args.get('asset_type'),
            'model': request.args.get('model'),
            'serial_number': request.args.get('serial_number'),
            'notes': request.args.get('notes'),
            'assigned_to': request.args.get('assigned_to'),
            'date_assigned_from': request.args.get('date_assigned_from'),
            'date_assigned_to': request.args.get('date_assigned_to'),
            'date_decommissioned_from': request.args.get('date_decommissioned_from'),
            'date_decommissioned_to': request.args.get('date_decommissioned_to')
        }
        
        logging.info(f"Fetching hardware items from database (page {page})")
        # Connect to database and execute queries
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause based on filters
            where_clauses = []
            params = []
            
            for field in ['site_name', 'room_number', 'room_name', 'asset_tag', 
                         'asset_type', 'model', 'serial_number', 'notes', 'assigned_to']:
                if filters[field]:
                    where_clauses.append(f"{field} LIKE ?")
                    params.append(f"%{filters[field]}%")
            
            if filters['date_assigned_from']:
                where_clauses.append("date_assigned >= ?")
                params.append(filters['date_assigned_from'])
            
            if filters['date_assigned_to']:
                where_clauses.append("date_assigned <= ?")
                params.append(filters['date_assigned_to'])
            
            if filters['date_decommissioned_from']:
                where_clauses.append("date_decommissioned >= ?")
                params.append(filters['date_decommissioned_from'])
            
            if filters['date_decommissioned_to']:
                where_clauses.append("date_decommissioned <= ?")
                params.append(filters['date_decommissioned_to'])
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count with filters
            count_sql = f"SELECT COUNT(*) FROM dbo.Formatted_Company_Inventory WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total_items = cursor.fetchval()
            logging.info(f"Total items: {total_items}")
            
            # Calculate pagination
            total_pages = (total_items + per_page - 1) // per_page
            
            # Get items for current page
            offset = (page - 1) * per_page
            query = f"""
            SELECT [asset_tag], [site_name], [room_number], [room_name], [asset_type],
                   [model], [serial_number], [notes], [assigned_to], [date_assigned], [date_decommissioned]
            FROM [dbo].[Formatted_Company_Inventory]
            WHERE {where_sql}
            ORDER BY [site_name], [room_number]
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY;
            """
            
            # Add pagination parameters
            query_params = params + [offset, per_page]
            
            logging.debug(f"Query SQL: {query}")
            logging.debug(f"Query params: {query_params}")
            
            cursor.execute(query, query_params)
            
            # Get column names and fetch rows
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            logging.info(f"Retrieved {len(rows)} rows")
            
            # Convert to list of dictionaries
            items = []
            for row in rows:
                item = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    item[columns[i].lower()] = value
                items.append(item)
            
            result = {
                'items': items,
                'total_pages': total_pages,
                'current_page': page,
                'total_items': total_items
            }
            
            logging.info("Successfully serialized items")
            return jsonify(result)
            
    except Exception as e:
        logging.error(f"Error in get_hardware: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': f'Database error: {str(e)}',
            'trace': traceback.format_exc()
        }), 500

@app.route('/api/hardware', methods=['POST'])
@role_required('add')
def add_hardware():
    try:
        data = request.json
        user_name = get_user_name()
        
        # Connect to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert new record
            query = """
            INSERT INTO dbo.Formatted_Company_Inventory 
            (site_name, room_number, room_name, asset_tag, asset_type,
             model, serial_number, notes, assigned_to, date_assigned, date_decommissioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            values = (
                data['site_name'],
                data['room_number'],
                data['room_name'],
                data['asset_tag'],
                data['asset_type'],
                data['model'],
                data['serial_number'],
                data.get('notes'),
                data.get('assigned_to'),
                data.get('date_assigned'),
                data.get('date_decommissioned')
            )
            
            cursor.execute(query, values)
            
            # Log audit entries for each field
            fields = ['site_name', 'room_number', 'room_name', 'asset_tag', 'asset_type',
                     'model', 'serial_number', 'notes', 'assigned_to', 'date_assigned', 'date_decommissioned']
            
            for field, value in zip(fields, values):
                if value is not None:  # Only log non-null values
                    log_audit(cursor, 'INSERT', data['asset_tag'], field, None, value, user_name)
            
            conn.commit()
            return jsonify({'message': 'Hardware added successfully'}), 201
            
    except Exception as e:
        logging.error(f"Error adding hardware: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 400

@app.route('/api/hardware/<asset_tag>', methods=['PUT'])
@role_required('edit')
def update_hardware(asset_tag):
    try:
        data = request.json
        user_name = get_user_name()
        
        # Connect to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get current values for audit logging
            cursor.execute("""
                SELECT site_name, room_number, room_name, asset_type, model,
                       serial_number, notes, assigned_to, date_assigned, date_decommissioned
                FROM dbo.Formatted_Company_Inventory
                WHERE asset_tag = ?
            """, (asset_tag,))
            
            current_values = cursor.fetchone()
            if not current_values:
                return jsonify({'error': 'Item not found'}), 404
            
            # Update record
            query = """
            UPDATE dbo.Formatted_Company_Inventory 
            SET site_name = ?,
                room_number = ?,
                room_name = ?,
                asset_type = ?,
                model = ?,
                serial_number = ?,
                notes = ?,
                assigned_to = ?,
                date_assigned = ?,
                date_decommissioned = ?
            WHERE asset_tag = ?;
            """
            
            new_values = (
                data['site_name'],
                data['room_number'],
                data['room_name'],
                data['asset_type'],
                data['model'],
                data['serial_number'],
                data.get('notes'),
                data.get('assigned_to'),
                data.get('date_assigned'),
                data.get('date_decommissioned'),
                asset_tag
            )
            
            cursor.execute(query, new_values)
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
            
            # Log audit entries for changed fields
            fields = ['site_name', 'room_number', 'room_name', 'asset_type', 'model',
                     'serial_number', 'notes', 'assigned_to', 'date_assigned', 'date_decommissioned']
            
            for i, field in enumerate(fields):
                if current_values[i] != new_values[i]:
                    log_audit(cursor, 'UPDATE', asset_tag, field, 
                             str(current_values[i]) if current_values[i] is not None else None,
                             str(new_values[i]) if new_values[i] is not None else None,
                             user_name)
            
            conn.commit()
            return jsonify({'message': 'Hardware updated successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error updating hardware: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 400

@app.route('/api/audit/<asset_tag>', methods=['GET'])
@role_required('view')
def get_audit_log(asset_tag):
    """Get audit log for a specific asset"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT action_type, field_name, old_value, new_value, changed_by, changed_at, notes
            FROM dbo.Inventory_Audit_Log
            WHERE asset_tag = ?
            ORDER BY changed_at DESC;
            """
            
            cursor.execute(query, (asset_tag,))
            
            # Get column names and fetch rows
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            audit_entries = []
            for row in rows:
                entry = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    entry[columns[i].lower()] = value
                audit_entries.append(entry)
            
            return jsonify(audit_entries)
            
    except Exception as e:
        logging.error(f"Error getting audit log: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': f'Database error: {str(e)}',
            'trace': traceback.format_exc()
        }), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True)
