from flask import Flask, render_template, request, jsonify, g
import pyodbc
from datetime import datetime
from utils import get_db_connection, log_change
from routes import location_routes

app = Flask(__name__)
app.register_blueprint(location_routes.bp)

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

@app.route('/api/test-db')
def test_db():
    try:
        cursor = g.db.cursor()
        cursor.execute("SELECT TOP 1 * FROM dbo.Formatted_Company_Inventory")
        result = cursor.fetchone()
        return jsonify({
            'success': True,
            'message': 'Database connection successful',
            'data': str(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT 
                location_id,
                site_name,
                room_number,
                room_name,
                room_type
            FROM dbo.Locations
            ORDER BY site_name, room_number
        """)
        
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations/types', methods=['GET'])
def get_room_types():
    try:
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT DISTINCT room_type
            FROM dbo.Locations
            ORDER BY room_type
        """)
        
        types = [row[0] for row in cursor.fetchall()]
        return jsonify(types)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Get query parameters
        room_type = request.args.get('room_type')
        page = int(request.args.get('page', 1))
        per_page = 25  # Fixed page size
        offset = (page - 1) * per_page
        
        # First get total count
        count_query = """
            SELECT COUNT(*)
            FROM dbo.Formatted_Company_Inventory i
            JOIN dbo.Locations l ON i.location_id = l.location_id
            WHERE 1=1
        """
        count_params = []
        
        if room_type:
            count_query += " AND l.room_type = ?"
            count_params.append(room_type)
            
        cursor.execute(count_query, count_params)
        total_items = cursor.fetchone()[0]
        
        # Base query for data
        query = """
            SELECT 
                i.inventory_id,
                l.site_name,
                l.room_number,
                l.room_name,
                l.room_type,
                i.asset_tag,
                i.asset_type,
                i.model,
                i.serial_number,
                i.notes,
                i.assigned_to,
                i.date_assigned,
                i.date_decommissioned,
                i.is_loaner
            FROM dbo.Formatted_Company_Inventory i
            JOIN dbo.Locations l ON i.location_id = l.location_id
            WHERE 1=1
        """
        params = []
        
        # Add room type filter if specified
        if room_type:
            query += " AND l.room_type = ?"
            params.append(room_type)
            
        # Add ORDER BY, OFFSET and FETCH NEXT
        query += """ 
            ORDER BY l.site_name, l.room_number, i.asset_tag
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, per_page])
        
        cursor.execute(query, params)
        
        columns = [column[0] for column in cursor.description]
        items = []
        
        for row in cursor.fetchall():
            items.append(dict(zip(columns, row)))
            
        return jsonify({
            'items': items,
            'total_items': total_items,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_items + per_page - 1) // per_page
        })
        
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
