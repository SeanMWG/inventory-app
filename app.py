from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for, flash
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import os
from flask_cors import CORS
from datetime import datetime
import msal
import requests
import logging
import sys
import pyodbc

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
app.secret_key = os.urandom(24)  # Required for session management
CORS(app)

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

# Initialize MSAL
def _build_msal_app():
    return msal.ConfidentialClientApplication(
        app.config['CLIENT_ID'],
        authority=app.config['AUTHORITY'],
        client_credential=None  # No client secret needed for public client application
    )

def _build_auth_url():
    return _build_msal_app().get_authorization_request_url(
        app.config['SCOPE'],
        redirect_uri=app.config['REDIRECT_URI'],
        state=None
    )

def _get_token_from_cache(token_cache):
    accounts = token_cache.get_accounts()
    if accounts:
        return _build_msal_app().acquire_token_silent(
            app.config['SCOPE'],
            account=accounts[0]
        )
    return None

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Function to get database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(db_connection)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        raise

# Auth routes
@app.route('/login')
def login():
    if session.get('user'):
        return redirect(url_for('serve_index'))
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('serve_index'))

@app.route(app.config['REDIRECT_PATH'])
def authorized():
    if request.args.get('error'):
        return request.args['error']
    
    cache = _build_msal_app().get_token_by_authorization_code(
        request.args['code'],
        scopes=app.config['SCOPE'],
        redirect_uri=app.config['REDIRECT_URI']
    )
    
    if 'error' in cache:
        return cache['error']
    
    session['user'] = cache.get('id_token_claims')
    return redirect(url_for('serve_index'))

# Protected routes
@app.route('/api/hardware', methods=['GET'])
# @login_required  # Temporarily disabled
def get_hardware():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 35
        
        # Get filter parameters
        filters = {
            'manufacturer': request.args.get('manufacturer'),
            'model_number': request.args.get('model_number'),
            'hardware_type': request.args.get('hardware_type'),
            'serial_number': request.args.get('serial_number'),
            'assigned_to': request.args.get('assigned_to'),
            'room_name': request.args.get('room_name'),
            'room_number': request.args.get('room_number'),
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
            
            if filters['manufacturer']:
                where_clauses.append("manufacturer LIKE ?")
                params.append(f"%{filters['manufacturer']}%")
            
            if filters['model_number']:
                where_clauses.append("model_number LIKE ?")
                params.append(f"%{filters['model_number']}%")
            
            if filters['hardware_type']:
                where_clauses.append("hardware_type LIKE ?")
                params.append(f"%{filters['hardware_type']}%")
            
            if filters['serial_number']:
                where_clauses.append("serial_number LIKE ?")
                params.append(f"%{filters['serial_number']}%")
            
            if filters['assigned_to']:
                where_clauses.append("assigned_to LIKE ?")
                params.append(f"%{filters['assigned_to']}%")
            
            if filters['room_name']:
                where_clauses.append("room_name LIKE ?")
                params.append(f"%{filters['room_name']}%")
            
            if filters['room_number']:
                where_clauses.append("room_number LIKE ?")
                params.append(f"%{filters['room_number']}%")
            
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
            SELECT [manufacturer], [model_number], [hardware_type], [serial_number],
                   [assigned_to], [room_name], [room_number], [date_assigned], [date_decommissioned]
            FROM [dbo].[Formatted_Company_Inventory]
            WHERE {where_sql}
            ORDER BY [serial_number]
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
            'total_items': total_items
        }
        
        logging.info("Successfully serialized items")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching hardware: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error fetching hardware: {str(e)}'}), 500

@app.route('/api/hardware', methods=['POST', 'PUT'])
# @login_required  # Temporarily disabled
def handle_hardware():
    if request.method == 'POST':
        return add_hardware()
    else:
        return update_hardware()

def add_hardware():
    try:
        data = request.json
        
        # Connect to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert new record
            query = """
            INSERT INTO dbo.Formatted_Company_Inventory 
            (manufacturer, model_number, hardware_type, serial_number, 
             assigned_to, room_name, room_number, date_assigned, date_decommissioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            cursor.execute(query, (
                data['manufacturer'],
                data['model_number'],
                data['hardware_type'],
                data['serial_number'],
                data.get('assigned_to'),
                data.get('room_name'),
                data.get('room_number'),
                data.get('date_assigned'),
                data.get('date_decommissioned')
            ))
            
            conn.commit()
            return jsonify({'message': 'Hardware added successfully'}), 201
            
    except Exception as e:
        logging.error(f"Error adding hardware: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Excel import route

@app.route('/api/import', methods=['POST'])
# @login_required  # Temporarily disabled
def import_excel():
    logging.info("Starting import process")
    
    if 'file' not in request.files:
        logging.error("No file in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logging.error("Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.xlsx'):
        logging.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Please upload an Excel file (.xlsx)'}), 400

    try:
        logging.info(f"Processing file: {file.filename}")
        # Create a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            logging.info(f"File saved to: {tmp.name}")
            
            # Read Excel file
            try:
                df = pd.read_excel(tmp.name)
                logging.info(f"Excel file read successfully")
                logging.info(f"Found columns: {df.columns.tolist()}")
                logging.info(f"First row: {df.iloc[0].to_dict()}")
            except Exception as e:
                logging.error(f"Error reading Excel file: {str(e)}")
                return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 400
            
            # Expected columns
            required_columns = ['manufacturer', 'model_number', 'hardware_type', 'serial_number']
            optional_columns = ['assigned_to', 'room_name', 'room_number', 'date_assigned', 'date_decommissioned']
            
            logging.info(f"Checking required columns: {required_columns}")
            
            # Verify required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f'Missing required columns: {", ".join(missing_columns)}. Found columns: {df.columns.tolist()}'
                logging.error(error_msg)
                return jsonify({'error': error_msg}), 400
            
            # Connect to database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                success_count = 0
                error_count = 0
                errors = []
                
                # Import records
                for index, row in df.iterrows():
                    try:
                        # Insert new record
                        query = """
                        INSERT INTO dbo.Formatted_Company_Inventory 
                        (manufacturer, model_number, hardware_type, serial_number, 
                         assigned_to, room_name, room_number, date_assigned, date_decommissioned)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """
                        
                        # Convert dates to string format if they exist
                        date_assigned = row.get('date_assigned')
                        date_decommissioned = row.get('date_decommissioned')
                        
                        if pd.notna(date_assigned):
                            date_assigned = pd.to_datetime(date_assigned).strftime('%Y-%m-%d')
                        else:
                            date_assigned = None
                            
                        if pd.notna(date_decommissioned):
                            date_decommissioned = pd.to_datetime(date_decommissioned).strftime('%Y-%m-%d')
                        else:
                            date_decommissioned = None
                        
                        cursor.execute(query, (
                            row['manufacturer'],
                            row['model_number'],
                            row['hardware_type'],
                            row['serial_number'],
                            row.get('assigned_to'),
                            row.get('room_name'),
                            row.get('room_number'),
                            date_assigned,
                            date_decommissioned
                        ))
                        conn.commit()
                        success_count += 1
                        
                    except Exception as e:
                        error_msg = f"Row {index + 2}: {str(e)}"
                        logging.error(f"Error processing row: {error_msg}")
                        logging.error(f"Row data: {row.to_dict()}")
                        error_count += 1
                        errors.append(error_msg)
            
            # Clean up temp file
            os.unlink(tmp.name)
            
            return jsonify({
                'message': f'Import completed. {success_count} records imported successfully, {error_count} failed.',
                'errors': errors
            })
                
    except Exception as e:
        error_msg = f'Error processing file: {str(e)}'
        logging.error(f"Unexpected error: {error_msg}")
        logging.error(f"Exception details:", exc_info=True)
        return jsonify({'error': error_msg}), 500

def update_hardware():
    try:
        data = request.json
        hardware_id = data.pop('id', None)  # Remove and get the ID
        
        if not hardware_id:
            return jsonify({'error': 'No ID provided'}), 400
        
        # Connect to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update record
            query = """
            UPDATE dbo.Formatted_Company_Inventory 
            SET manufacturer = ?,
                model_number = ?,
                hardware_type = ?,
                serial_number = ?,
                assigned_to = ?,
                room_name = ?,
                room_number = ?,
                date_assigned = ?,
                date_decommissioned = ?
            WHERE id = ?;
            """
            
            cursor.execute(query, (
                data['manufacturer'],
                data['model_number'],
                data['hardware_type'],
                data['serial_number'],
                data.get('assigned_to'),
                data.get('room_name'),
                data.get('room_number'),
                data.get('date_assigned'),
                data.get('date_decommissioned'),
                hardware_id
            ))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Item not found'}), 404
            
            conn.commit()
            return jsonify({'message': 'Hardware updated successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error updating hardware: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
