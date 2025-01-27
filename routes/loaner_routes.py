from flask import Blueprint, jsonify, request
from datetime import datetime
import pyodbc
from utils import get_db_connection, log_change

loaner_bp = Blueprint('loaner_routes', __name__)

@loaner_bp.route('/api/loaners/available')
def get_available_loaners():
    """Get all available loaner devices"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM dbo.AvailableLoaners')
        columns = [column[0] for column in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@loaner_bp.route('/api/loaners/checked-out')
def get_checked_out_loaners():
    """Get all currently checked out loaner devices"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM dbo.CheckedOutLoaners')
        columns = [column[0] for column in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@loaner_bp.route('/api/loaners/checkout', methods=['POST'])
def checkout_loaner():
    """Check out a loaner device"""
    try:
        data = request.get_json()
        inventory_id = data.get('inventory_id')
        user_name = data.get('user_name')
        expected_return_date = data.get('expected_return_date')
        notes = data.get('notes')
        
        if not all([inventory_id, user_name]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First verify the item is available
        cursor.execute('''
            SELECT inventory_id FROM dbo.AvailableLoaners 
            WHERE inventory_id = ?
        ''', inventory_id)
        
        if not cursor.fetchone():
            return jsonify({'error': 'Item is not available for checkout'}), 400
        
        # Create checkout record
        cursor.execute('''
            INSERT INTO dbo.LoanerCheckouts (
                inventory_id, user_name, checkout_date, 
                expected_return_date, checkout_notes
            ) VALUES (?, ?, GETDATE(), ?, ?)
        ''', (inventory_id, user_name, expected_return_date, notes))
        
        # Log the change
        log_change(
            cursor=cursor,
            asset_tag=None,  # We'll get this from a subquery
            action_type='CHECKOUT',
            field_name='status',
            old_value='available',
            new_value='checked out',
            changed_by=user_name
        )
        
        conn.commit()
        return jsonify({'message': 'Checkout successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@loaner_bp.route('/api/loaners/checkin', methods=['POST'])
def checkin_loaner():
    """Check in a loaner device"""
    try:
        data = request.get_json()
        checkout_id = data.get('checkout_id')
        
        if not checkout_id:
            return jsonify({'error': 'Missing checkout_id'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get checkout info before updating
        cursor.execute('''
            SELECT lc.inventory_id, lc.user_name, i.asset_tag
            FROM dbo.LoanerCheckouts lc
            JOIN dbo.Formatted_Company_Inventory i ON i.inventory_id = lc.inventory_id
            WHERE lc.checkout_id = ? AND lc.checkin_date IS NULL
        ''', checkout_id)
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Invalid checkout or already checked in'}), 400
            
        inventory_id, user_name, asset_tag = result
        
        # Update checkout record
        cursor.execute('''
            UPDATE dbo.LoanerCheckouts 
            SET checkin_date = GETDATE()
            WHERE checkout_id = ?
        ''', checkout_id)
        
        # Log the change
        log_change(
            cursor=cursor,
            asset_tag=asset_tag,
            action_type='CHECKIN',
            field_name='status',
            old_value='checked out',
            new_value='available',
            changed_by=user_name
        )
        
        conn.commit()
        return jsonify({'message': 'Check-in successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@loaner_bp.route('/loaners')
def loaner_management():
    """Render the loaner management page"""
    from flask import render_template
    return render_template('loaner_management.html')
