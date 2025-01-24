from flask import Flask, render_template, request, jsonify, g
import pyodbc
from datetime import datetime
from utils import get_db_connection, log_change

app = Flask(__name__)

@app.before_request
def before_request():
    g.db = get_db_connection()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/hardware/<asset_tag>/toggle-loaner', methods=['POST'])
def toggle_loaner_status(asset_tag):
    try:
        cursor = g.db.cursor()
        
        # Get current loaner status
        cursor.execute("""
            SELECT inventory_id, is_loaner 
            FROM dbo.Formatted_Company_Inventory 
            WHERE asset_tag = ?
        """, asset_tag)
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Asset not found'}), 404
            
        inventory_id, current_status = result
        new_status = not current_status
        
        # Update loaner status
        cursor.execute("""
            UPDATE dbo.Formatted_Company_Inventory 
            SET is_loaner = ?
            WHERE inventory_id = ?
        """, new_status, inventory_id)
        
        # Log the change
        log_change(
            cursor=cursor,
            asset_tag=asset_tag,
            action_type='UPDATE',
            field_name='is_loaner',
            old_value=str(current_status),
            new_value=str(new_status),
            changed_by=request.headers.get('X-User-ID', 'system')
        )
        
        g.db.commit()
        
        return jsonify({
            'success': True,
            'is_loaner': new_status
        })
        
    except Exception as e:
        g.db.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware', methods=['GET'])
def get_hardware():
    try:
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT 
                inventory_id,
                site_name,
                room_number,
                room_name,
                asset_tag,
                asset_type,
                model,
                serial_number,
                notes,
                assigned_to,
                date_assigned,
                date_decommissioned,
                is_loaner
            FROM dbo.Formatted_Company_Inventory
            ORDER BY site_name, room_number, asset_tag
        """)
        
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/<asset_tag>/audit', methods=['GET'])
def get_audit_log(asset_tag):
    try:
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT 
                changed_at,
                action_type,
                field_name,
                old_value,
                new_value,
                changed_by
            FROM dbo.AuditLog
            WHERE asset_tag = ?
            ORDER BY changed_at DESC
        """, asset_tag)
        
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
