from flask import Flask, request, jsonify, render_template, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
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
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/hardware', methods=['GET'])
def get_hardware():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 35
        
        # Get paginated items
        pagination = Hardware.query.order_by(Hardware.serial_number).paginate(
            page=page, per_page=per_page, error_out=False)
        
        items = [{
            'id': item.id,
            'manufacturer': item.manufacturer,
            'model_number': item.model_number,
            'hardware_type': item.hardware_type,
            'serial_number': item.serial_number,
            'assigned_to': item.assigned_to,
            'location': item.location,
            'date_assigned': item.date_assigned.isoformat() if item.date_assigned else None,
            'date_decommissioned': item.date_decommissioned.isoformat() if item.date_decommissioned else None
        } for item in pagination.items]
        
        return jsonify({
            'items': items,
            'total_pages': pagination.pages,
            'current_page': page,
            'total_items': pagination.total
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware', methods=['POST'])
def add_hardware():
    try:
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
        db.session.commit()
        return jsonify({'message': 'Hardware added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/')
def serve_index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
