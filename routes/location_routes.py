from flask import Blueprint, request, jsonify, g
from utils import log_change

bp = Blueprint('locations', __name__)

@bp.route('/api/locations', methods=['POST'])
def create_location():
    try:
        data = request.get_json()
        required_fields = ['site_name', 'room_number', 'room_name', 'room_type']
        
        # Validate required fields
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        cursor = g.db.cursor()
        
        # Check if location already exists
        cursor.execute("""
            SELECT location_id FROM dbo.Locations 
            WHERE site_name = ? AND room_number = ?
        """, (data['site_name'], data['room_number']))
        
        if cursor.fetchone():
            return jsonify({'error': 'Location already exists'}), 409

        # Insert new location
        cursor.execute("""
            INSERT INTO dbo.Locations (site_name, room_number, room_name, room_type)
            VALUES (?, ?, ?, ?);
            SELECT SCOPE_IDENTITY() as location_id;
        """, (
            data['site_name'],
            data['room_number'],
            data['room_name'],
            data['room_type']
        ))
        
        location_id = cursor.fetchone()[0]

        # Log the creation
        log_change(
            cursor=cursor,
            asset_tag=f"LOC_{location_id}",  # Use location_id as reference
            action_type='CREATE',
            field_name='location',
            old_value=None,
            new_value=f"{data['site_name']} - {data['room_number']}",
            changed_by=request.headers.get('X-User-ID', 'system')
        )
        
        g.db.commit()
        
        return jsonify({
            'success': True,
            'location_id': location_id,
            'message': 'Location created successfully'
        })
        
    except Exception as e:
        g.db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/locations/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    try:
        data = request.get_json()
        cursor = g.db.cursor()
        
        # Check if location exists
        cursor.execute("SELECT * FROM dbo.Locations WHERE location_id = ?", (location_id,))
        location = cursor.fetchone()
        if not location:
            return jsonify({'error': 'Location not found'}), 404

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if 'site_name' in data:
            update_fields.append("site_name = ?")
            params.append(data['site_name'])
        
        if 'room_number' in data:
            update_fields.append("room_number = ?")
            params.append(data['room_number'])
        
        if 'room_name' in data:
            update_fields.append("room_name = ?")
            params.append(data['room_name'])
        
        if 'room_type' in data:
            update_fields.append("room_type = ?")
            params.append(data['room_type'])
            
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
            
        # Add location_id to params
        params.append(location_id)
        
        # Get old values for logging
        old_values = dict(zip(
            ['site_name', 'room_number', 'room_name', 'room_type'],
            location
        ))

        # Execute update
        cursor.execute(f"""
            UPDATE dbo.Locations 
            SET {', '.join(update_fields)}
            WHERE location_id = ?
        """, params)

        # Log each changed field
        for field in ['site_name', 'room_number', 'room_name', 'room_type']:
            if field in data and data[field] != old_values[field]:
                log_change(
                    cursor=cursor,
                    asset_tag=f"LOC_{location_id}",
                    action_type='UPDATE',
                    field_name=field,
                    old_value=old_values[field],
                    new_value=data[field],
                    changed_by=request.headers.get('X-User-ID', 'system')
                )
        
        g.db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully'
        })
        
    except Exception as e:
        g.db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    try:
        cursor = g.db.cursor()
        
        # Check if location exists
        cursor.execute("SELECT * FROM dbo.Locations WHERE location_id = ?", (location_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Location not found'}), 404
            
        # Check if location is in use
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM dbo.Formatted_Company_Inventory 
            WHERE location_id = ?
        """, (location_id,))
        
        if cursor.fetchone()[0] > 0:
            return jsonify({
                'error': 'Cannot delete location that has inventory items assigned to it'
            }), 400
            
        # Get location details for logging
        cursor.execute("""
            SELECT site_name, room_number
            FROM dbo.Locations 
            WHERE location_id = ?
        """, (location_id,))
        location = cursor.fetchone()
        
        # Delete location
        cursor.execute("DELETE FROM dbo.Locations WHERE location_id = ?", (location_id,))

        # Log the deletion
        log_change(
            cursor=cursor,
            asset_tag=f"LOC_{location_id}",
            action_type='DELETE',
            field_name='location',
            old_value=f"{location[0]} - {location[1]}",
            new_value=None,
            changed_by=request.headers.get('X-User-ID', 'system')
        )
        
        g.db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location deleted successfully'
        })
        
    except Exception as e:
        g.db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/locations/validate', methods=['POST'])
def validate_location():
    try:
        data = request.get_json()
        cursor = g.db.cursor()
        
        # Check if site_name and room_number combination exists
        cursor.execute("""
            SELECT location_id 
            FROM dbo.Locations 
            WHERE site_name = ? AND room_number = ?
        """, (data.get('site_name'), data.get('room_number')))
        
        existing = cursor.fetchone()
        
        return jsonify({
            'exists': existing is not None,
            'location_id': existing[0] if existing else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
