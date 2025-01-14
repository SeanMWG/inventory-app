from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Error handler for API routes
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {str(error)}")
    return jsonify({"error": str(error)}), 500

# Get database connection string from environment variable and format it for SQLAlchemy
try:
    db_connection = os.getenv('DATABASE_URL', 'sqlite:///inventory.db')
    logger.info(f"Database type: {'SQL Server' if 'ODBC Driver' in db_connection else 'SQLite'}")
    
    if 'ODBC Driver' in db_connection:
        # Parse the ODBC connection string
        params = dict(param.split('=') for param in db_connection.split(';') if '=' in param)
        # Format it as a SQLAlchemy URL
        sql_server_url = f"mssql+pyodbc:///?odbc_connect={db_connection}"
        app.config['SQLALCHEMY_DATABASE_URI'] = sql_server_url
        logger.info("Successfully configured SQL Server connection")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_connection
        logger.info("Using SQLite database")
except Exception as e:
    logger.error(f"Error configuring database: {str(e)}")
    raise
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/api/hardware', methods=['GET'])
def get_hardware():
    hardware_items = Hardware.query.all()
    return jsonify([{
        'id': item.id,
        'manufacturer': item.manufacturer,
        'model_number': item.model_number,
        'hardware_type': item.hardware_type,
        'serial_number': item.serial_number,
        'assigned_to': item.assigned_to,
        'location': item.location,
        'date_assigned': item.date_assigned.isoformat() if item.date_assigned else None,
        'date_decommissioned': item.date_decommissioned.isoformat() if item.date_decommissioned else None
    } for item in hardware_items])

@app.route('/api/hardware', methods=['POST'])
def add_hardware():
    data = request.json
    
    # Convert date strings to datetime objects if they exist
    date_assigned = datetime.fromisoformat(data['date_assigned']) if data.get('date_assigned') else None
    date_decommissioned = datetime.fromisoformat(data['date_decommissioned']) if data.get('date_decommissioned') else None
    
    new_hardware = Hardware(
        manufacturer=data['manufacturer'],
        model_number=data['model_number'],
        hardware_type=data['hardware_type'],
        serial_number=data['serial_number'],
        assigned_to=data.get('assigned_to'),
        location=data.get('location'),
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

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 8000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting app: {e}")
