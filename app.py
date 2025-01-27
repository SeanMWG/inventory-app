from flask import Flask, request, jsonify, render_template, redirect, session, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import msal
import pyodbc
import logging

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.urandom(24)  # Required for session management

# Configure CORS
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["https://inventory-app-sean.azurewebsites.net", "https://login.microsoftonline.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy for database models
db = SQLAlchemy(app)

# Initialize MSAL
def _build_msal_app():
    return msal.ConfidentialClientApplication(
        app.config['CLIENT_ID'],
        authority=app.config['AUTHORITY'],
        client_credential=app.config['CLIENT_SECRET']
    )

def _build_auth_url():
    return _build_msal_app().get_authorization_request_url(
        app.config['SCOPE'],
        redirect_uri=app.config['REDIRECT_URI'],
        state=session.get('state', '')
    )

def _get_token_from_cache():
    cache = _build_msal_app().get_token_cache()
    accounts = cache.find(app.config['SCOPE'])
    if accounts:
        result = _build_msal_app().acquire_token_silent(
            app.config['SCOPE'],
            account=accounts[0]
        )
        return result

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Database connection
def get_db_connection():
    """Get a connection to the SQL Server database"""
    conn_str = app.config['DATABASE_URL']
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable is not set")
    return pyodbc.connect(conn_str)

# Hardware Model
class Hardware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(100), nullable=False)
    model_number = db.Column(db.String(100), nullable=False)
    hardware_type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    assigned_to = db.Column(db.String(100))
    location = db.Column(db.String(100))
    date_assigned = db.Column(db.DateTime)
    date_decommissioned = db.Column(db.DateTime)

# Auth routes
@app.route('/login')
def login():
    if session.get('user'):
        return redirect(url_for('serve_index'))
    session['state'] = os.urandom(16).hex()
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('serve_index'))

@app.route(app.config['REDIRECT_PATH'])
def authorized():
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('login'))
    
    if request.args.get('code'):
        result = _build_msal_app().acquire_token_by_authorization_code(
            request.args['code'],
            scopes=app.config['SCOPE'],
            redirect_uri=app.config['REDIRECT_URI']
        )
        if 'error' in result:
            return result['error']
        session['user'] = result.get('id_token_claims')
        return redirect(url_for('serve_index'))
    return redirect(url_for('login'))

# API Routes
@app.route('/api/hardware', methods=['GET', 'OPTIONS'])
@login_required
def get_hardware():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 35
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM dbo.Formatted_Company_Inventory')
        total_items = cursor.fetchone()[0]
        
        # Get paginated items
        cursor.execute('''
            SELECT manufacturer, model_number, hardware_type, serial_number, 
                   assigned_to, location, date_assigned, date_decommissioned
            FROM dbo.Formatted_Company_Inventory
            ORDER BY serial_number
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        ''', (offset, per_page))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'manufacturer': row[0],
                'model_number': row[1],
                'hardware_type': row[2],
                'serial_number': row[3],
                'assigned_to': row[4],
                'location': row[5],
                'date_assigned': row[6].isoformat() if row[6] else None,
                'date_decommissioned': row[7].isoformat() if row[7] else None
            })
        
        total_pages = (total_items + per_page - 1) // per_page
        
        return jsonify({
            'items': items,
            'total_pages': total_pages,
            'current_page': page,
            'total_items': total_items
        })
    except Exception as e:
        logger.error(f"Error getting hardware: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/hardware', methods=['POST', 'OPTIONS'])
@login_required
def add_hardware():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert date strings to datetime objects if they exist
        date_assigned = datetime.fromisoformat(data['date_assigned']) if data.get('date_assigned') else None
        date_decommissioned = datetime.fromisoformat(data['date_decommissioned']) if data.get('date_decommissioned') else None
        
        cursor.execute('''
            INSERT INTO dbo.Formatted_Company_Inventory 
            (manufacturer, model_number, hardware_type, serial_number, assigned_to, location, date_assigned, date_decommissioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['manufacturer'],
            data['model_number'],
            data['hardware_type'],
            data['serial_number'],
            data.get('assigned_to'),
            data.get('location'),
            date_assigned,
            date_decommissioned
        ))
        
        conn.commit()
        return jsonify({'message': 'Hardware added successfully'}), 201
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/')
def serve_index():
    user = session.get('user', {})
    return render_template('index.html', user=user)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Add CORS headers after request
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ['https://inventory-app-sean.azurewebsites.net', 'https://login.microsoftonline.com']:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
    return response

if __name__ == '__main__':
    app.run(debug=True)
