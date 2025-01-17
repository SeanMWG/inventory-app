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
            SELECT [site_name], [room_number], [room_name], [asset_tag], [asset_type],
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
            items = []
            for row in rows:
                item = {}
                for i, value in enumerate(row):
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

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True)
