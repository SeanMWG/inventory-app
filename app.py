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
logging.info("Checking database configuration...")
logging.info(f"Database URL exists: {bool(db_connection)}")

def get_db_connection():
    """Get database connection with better error handling"""
    try:
        # Use the provided connection string
        logging.info("Attempting database connection")
        return pyodbc.connect(db_connection)
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        logging.error(traceback.format_exc())
        raise

@app.route('/api/hardware', methods=['GET'])
def get_hardware():
    """Get hardware items with better error handling"""
    try:
        logging.info("GET /api/hardware request received")
        
        # Test database connection first
        logging.info("Testing database connection...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Simple test query
            cursor.execute("SELECT TOP 1 * FROM dbo.Formatted_Company_Inventory")
            test_row = cursor.fetchone()
            logging.info(f"Test query successful: {bool(test_row)}")
            
            # If test successful, proceed with actual query
            query = """
            SELECT TOP 35 [id], [site_name], [room_number], [room_name], [asset_tag], 
                   [asset_type], [model], [serial_number], [notes], [assigned_to], 
                   [date_assigned], [date_decommissioned]
            FROM [dbo].[Formatted_Company_Inventory]
            ORDER BY [site_name], [room_number]
            """
            
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            items = []
            for row in rows:
                item = {}
                for i, value in enumerate(row):
                    item[columns[i].lower()] = value
                items.append(item)
            
            result = {
                'items': items,
                'total_pages': 1,
                'current_page': 1,
                'total_items': len(items)
            }
            
            return jsonify(result)
            
    except Exception as e:
        logging.error(f"Error in get_hardware: {str(e)}")
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
