from flask import Flask, request, jsonify, render_template, redirect, session, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import msal
import pyodbc
import logging
import traceback

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.urandom(24)  # Required for session management
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MSAL
def _build_msal_app():
    try:
        if not app.config.get('CLIENT_ID'):
            raise ValueError("CLIENT_ID not set in configuration")
        if not app.config.get('AUTHORITY'):
            raise ValueError("AUTHORITY not set in configuration")
        if not app.config.get('CLIENT_SECRET'):
            raise ValueError("CLIENT_SECRET not set in configuration")
            
        return msal.ConfidentialClientApplication(
            app.config['CLIENT_ID'],
            authority=app.config['AUTHORITY'],
            client_credential=app.config['CLIENT_SECRET']
        )
    except Exception as e:
        logger.error(f"Error building MSAL app: {str(e)}\n{traceback.format_exc()}")
        raise

def _build_auth_url():
    try:
        if not app.config.get('SCOPE'):
            raise ValueError("SCOPE not set in configuration")
        if not app.config.get('REDIRECT_URI'):
            raise ValueError("REDIRECT_URI not set in configuration")
            
        return _build_msal_app().get_authorization_request_url(
            app.config['SCOPE'],
            redirect_uri=app.config['REDIRECT_URI'],
            state=session.get('state', '')
        )
    except Exception as e:
        logger.error(f"Error building auth URL: {str(e)}\n{traceback.format_exc()}")
        raise

def _get_token_from_cache():
    try:
        cache = _build_msal_app().get_token_cache()
        accounts = cache.find(app.config['SCOPE'])
        if accounts:
            result = _build_msal_app().acquire_token_silent(
                app.config['SCOPE'],
                account=accounts[0]
            )
            return result
    except Exception as e:
        logger.error(f"Error getting token from cache: {str(e)}\n{traceback.format_exc()}")
        return None

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
    try:
        conn_str = app.config['DATABASE_URL']
        if not conn_str:
            raise ValueError("DATABASE_URL environment variable is not set")
        return pyodbc.connect(conn_str)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}\n{traceback.format_exc()}")
        raise

# Auth routes
@app.route('/login')
def login():
    try:
        if session.get('user'):
            return redirect(url_for('serve_index'))
        session['state'] = os.urandom(16).hex()
        auth_url = _build_auth_url()
        logger.info(f"Built auth URL: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        error_msg = f"Login error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg, 500

@app.route('/logout')
def logout():
    try:
        session.clear()
        return redirect(url_for('serve_index'))
    except Exception as e:
        error_msg = f"Logout error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg, 500

@app.route(app.config['REDIRECT_PATH'])
def authorized():
    try:
        if request.args.get('state') != session.get('state'):
            logger.error("State mismatch in authorized route")
            return redirect(url_for('login'))
        
        if 'error' in request.args:
            error_msg = f"Error in auth response: {request.args['error']}"
            logger.error(error_msg)
            return error_msg
        
        if request.args.get('code'):
            logger.info("Got authorization code, acquiring token")
            result = _build_msal_app().acquire_token_by_authorization_code(
                request.args['code'],
                scopes=app.config['SCOPE'],
                redirect_uri=app.config['REDIRECT_URI']
            )
            if 'error' in result:
                error_msg = f"Error acquiring token: {result['error']}"
                logger.error(error_msg)
                return error_msg
            session['user'] = result.get('id_token_claims')
            logger.info("Successfully acquired token and set user session")
            return redirect(url_for('serve_index'))
        return redirect(url_for('login'))
    except Exception as e:
        error_msg = f"Authorization error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg, 500

# API Routes
@app.route('/api/hardware', methods=['GET'])
@login_required
def get_hardware():
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
        error_msg = f"Error getting hardware: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/hardware', methods=['POST'])
@login_required
def add_hardware():
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
        error_msg = f"Error adding hardware: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': error_msg}), 400
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/')
def serve_index():
    try:
        user = session.get('user', {})
        logger.info(f"Serving index for user: {user.get('name', 'Anonymous')}")
        return render_template('index.html', user=user)
    except Exception as e:
        error_msg = f"Error serving index: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg, 500

@app.route('/static/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('static', path)
    except Exception as e:
        error_msg = f"Error serving static file {path}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg, 500

if __name__ == '__main__':
    app.run(debug=True)
