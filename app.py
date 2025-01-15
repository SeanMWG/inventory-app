from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for, flash
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import os
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import msal
import requests

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.urandom(24)  # Required for session management
CORS(app)

# Configure database
db_connection = os.getenv('DATABASE_URL', 'sqlite:///inventory.db')
if 'ODBC Driver' in db_connection:
    # Parse the ODBC connection string
    params = dict(param.split('=') for param in db_connection.split(';') if '=' in param)
    # Format it as a SQLAlchemy URL
    sql_server_url = f"mssql+pyodbc:///?odbc_connect={db_connection}"
    app.config['SQLALCHEMY_DATABASE_URI'] = sql_server_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_connection

# Initialize SQLAlchemy
db = SQLAlchemy(app)

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

# Hardware Model
class Hardware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(100), nullable=False)
    model_number = db.Column(db.String(100), nullable=False)
    hardware_type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    assigned_to = db.Column(db.String(100))
    room_name = db.Column(db.String(100))
    date_assigned = db.Column(db.DateTime)
    date_decommissioned = db.Column(db.DateTime)

# Create tables
with app.app_context():
    db.create_all()

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
@login_required
def get_hardware():
    hardware_items = Hardware.query.all()
    return jsonify([{
        'id': item.id,
        'manufacturer': item.manufacturer,
        'model_number': item.model_number,
        'hardware_type': item.hardware_type,
        'serial_number': item.serial_number,
        'assigned_to': item.assigned_to,
        'room_name': item.room_name,
        'date_assigned': item.date_assigned.isoformat() if item.date_assigned else None,
        'date_decommissioned': item.date_decommissioned.isoformat() if item.date_decommissioned else None
    } for item in hardware_items])

@app.route('/api/hardware', methods=['POST'])
@login_required
def add_hardware():
    data = request.json
    
    date_assigned = datetime.fromisoformat(data['date_assigned']) if data.get('date_assigned') else None
    date_decommissioned = datetime.fromisoformat(data['date_decommissioned']) if data.get('date_decommissioned') else None
    
    new_hardware = Hardware(
        manufacturer=data['manufacturer'],
        model_number=data['model_number'],
        hardware_type=data['hardware_type'],
        serial_number=data['serial_number'],
        assigned_to=data.get('assigned_to'),
        room_name=data.get('room_name'),
        date_assigned=date_assigned,
        date_decommissioned=date_decommissioned
    )
    
    db.session.add(new_hardware)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Hardware added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Excel import route
@app.route('/api/import', methods=['POST'])
@login_required
def import_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Please upload an Excel file (.xlsx)'}), 400

    try:
        print("Starting Excel import...")  # Debug log
        # Create a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            print(f"File saved to temp location: {tmp.name}")  # Debug log
            
            # Read Excel file
            try:
                df = pd.read_excel(tmp.name)
                print(f"Excel file read successfully. Columns: {df.columns.tolist()}")  # Debug log
            except Exception as e:
                print(f"Error reading Excel file: {str(e)}")  # Debug log
                return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 400
            
            # Expected columns
            required_columns = ['manufacturer', 'model_number', 'hardware_type', 'serial_number']
            optional_columns = ['assigned_to', 'room_name', 'date_assigned', 'date_decommissioned']
            
            print(f"Required columns: {required_columns}")  # Debug log
            print(f"Found columns: {df.columns.tolist()}")  # Debug log
            
            # Verify required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f'Missing required columns: {", ".join(missing_columns)}'
                print(f"Error: {error_msg}")  # Debug log
                return jsonify({'error': error_msg}), 400
            
            # Import records
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Create hardware object
                    hardware = Hardware(
                        manufacturer=row['manufacturer'],
                        model_number=row['model_number'],
                        hardware_type=row['hardware_type'],
                        serial_number=row['serial_number'],
                        assigned_to=row.get('assigned_to'),
                        room_name=row.get('room_name'),
                        date_assigned=pd.to_datetime(row.get('date_assigned')).to_pydatetime() if pd.notna(row.get('date_assigned')) else None,
                        date_decommissioned=pd.to_datetime(row.get('date_decommissioned')).to_pydatetime() if pd.notna(row.get('date_decommissioned')) else None
                    )
                    db.session.add(hardware)
                    db.session.commit()
                    success_count += 1
                except Exception as e:
                    error_msg = f"Row {index + 2}: {str(e)}"
                    print(f"Error processing row: {error_msg}")  # Debug log
                    error_count += 1
                    errors.append(error_msg)
                    db.session.rollback()
            
            # Clean up temp file
            os.unlink(tmp.name)
            
            return jsonify({
                'message': f'Import completed. {success_count} records imported successfully, {error_count} failed.',
                'errors': errors
            })
                
    except Exception as e:
        error_msg = f'Error processing file: {str(e)}'
        print(f"Error: {error_msg}")  # Debug log
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True)
