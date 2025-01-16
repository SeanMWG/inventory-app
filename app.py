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
logging.info(f"Original connection string: {db_connection}")

if 'ODBC Driver' in db_connection:
    try:
        # Test connection immediately
        test_conn = pyodbc.connect(db_connection)
        test_conn.close()
        logging.info("Database connection test successful")
    except Exception as e:
        logging.error(f"Error testing database connection: {str(e)}")
        # Try a simpler connection string
        params = dict(param.split('=') for param in db_connection.split(';') if '=' in param)
        db_connection = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={params.get('Server')};"
            f"DATABASE={params.get('Database')};"
            "Trusted_Connection=yes;"
        )
        logging.info(f"Using fallback connection string: {db_connection}")

def get_user_role():
    """Get the user's role from Azure AD claims"""
    headers = request.headers
    roles = headers.get('X-MS-CLIENT-PRINCIPAL-ROLES', '').split(',')
    
    # Map Azure AD roles to app roles
    for role in roles:
        role = role.lower().strip()
        if role in app.config['ROLES']:
            return role
    
    # Return default role if no matching role found
    return app.config['DEFAULT_ROLE']

def has_permission(required_permission):
    """Check if the current user has the required permission"""
    user_role = get_user_role()
    if not user_role:
        return False
    
    role_permissions = app.config['ROLE_PERMISSIONS'].get(user_role, [])
    return required_permission in role_permissions

def role_required(permission):
    """Decorator to require specific permission for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_permission(permission):
                return jsonify({
                    'error': 'Permission denied',
                    'required_permission': permission
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Function to get database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(db_connection)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        raise

# Protected routes
@app.route('/api/hardware', methods=['GET'])
@role_required('view')
def get_hardware():
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
            SELECT [id], [site_name], [room_number], [room_name], [asset_tag], [asset_type],
                   [model], [serial_number], [notes], [assigned_to], [date_assigned], [date_decommissioned]
            FROM [dbo].[Formatted_Company_Inventory]
            WHERE {where_sql}
            ORDER BY [site_name], [room_number]
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY;
            """
            
            # Add pagination parameters
            query_params = params + [offset, per_page]
            
            logging.info(f"Executing query for page {page} (offset {offset})...")
            cursor.execute(query, query_params)
            
            # Get column names and fetch rows
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            logging.info(f"Retrieved {len(rows)} rows")
            
            # Convert to list of dictionaries
            hardware_items = []
            for row in rows:
                item = {}
                for i, value in enumerate(row):
                    item[columns[i].lower()] = value
                hardware_items.append(item)
            
            if hardware_items:
                logging.info(f"Sample item: {hardware_items[0]}")
        logging.info(f"Found {len(hardware_items)} items on page {page}")
        
        result = {
            'items': hardware_items,
            'total_pages': total_pages,
            'current_page': page,
            'total_items': total_items,
            'user_role': get_user_role()  # Include user role in response
        }
        
        logging.info("Successfully serialized items")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching hardware: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error fetching hardware: {str(e)}'}), 500

@app.route('/api/hardware', methods=['POST'])
@role_required('add')
def add_hardware():
    try:
        data = request.json
        
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
            
            cursor.execute(query, (
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
            ))
            
            conn.commit()
            return jsonify({'message': 'Hardware added successfully'}), 201
            
    except Exception as e:
        logging.error(f"Error adding hardware: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/api/hardware/<int:id>', methods=['PUT'])
@role_required('edit')
def update_hardware(id):
    try:
        data = request.json
        
        # Connect to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update record
            query = """
            UPDATE dbo.Formatted_Company_Inventory 
            SET site_name = ?,
                room_number = ?,
                room_name = ?,
                asset_tag = ?,
                asset_type = ?,
                model = ?,
                serial_number = ?,
                notes = ?,
                assigned_to = ?,
                date_assigned = ?,
                date_decommissioned = ?
            WHERE id = ?;
            """
            
            cursor.execute(query, (
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
                data.get('date_decommissioned'),
                id
            ))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
            
            conn.commit()
            return jsonify({'message': 'Hardware updated successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error updating hardware: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/')
@role_required('view')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
@role_required('view')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/user/role')
def get_user_role_api():
    """API endpoint to get the current user's role"""
    role = get_user_role()
    return jsonify({
        'role': role,
        'permissions': app.config['ROLE_PERMISSIONS'].get(role, [])
    })

if __name__ == '__main__':
    app.run(debug=True)
