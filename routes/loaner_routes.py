from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from app import get_db_connection, log_audit, get_user_name, role_required

loaner_bp = Blueprint('loaner_bp', __name__)

@loaner_bp.route('/api/loaners/available', methods=['GET'])
@role_required('view')
def get_available_loaners():
    """Get list of available loaner items"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dbo.AvailableLoaners")
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch and convert to list of dictionaries
            items = []
            for row in cursor.fetchall():
                item = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    item[columns[i].lower()] = value
                items.append(item)
            
            return jsonify(items)
            
    except Exception as e:
        logging.error(f"Error getting available loaners: {str(e)}")
        return jsonify({'error': str(e)}), 500

@loaner_bp.route('/api/loaners/checked-out', methods=['GET'])
@role_required('view')
def get_checked_out_loaners():
    """Get list of checked out loaner items"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dbo.CheckedOutLoaners")
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch and convert to list of dictionaries
            items = []
            for row in cursor.fetchall():
                item = {}
                for i, value in enumerate(row):
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    item[columns[i].lower()] = value
                items.append(item)
            
            return jsonify(items)
            
    except Exception as e:
        logging.error(f"Error getting checked out loaners: {str(e)}")
        return jsonify({'error': str(e)}), 500

@loaner_bp.route('/api/loaners/checkout', methods=['POST'])
@role_required('edit')
def checkout_item():
    """Check out a loaner item"""
    try:
        data = request.json
        user_name = get_user_name()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert checkout record
            query = """
            INSERT INTO dbo.LoanerCheckouts 
            (inventory_id, user_name, expected_return_date, notes)
            VALUES (?, ?, ?, ?);
            """
            
            cursor.execute(query, (
                data['inventory_id'],
                data['user_name'],
                data.get('expected_return_date'),
                data.get('notes')
            ))
            
            # Log the checkout
            log_audit(cursor, 'CHECKOUT', None, 'loaner_status', 'available', 'checked_out', user_name)
            
            conn.commit()
            return jsonify({'message': 'Item checked out successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error checking out item: {str(e)}")
        return jsonify({'error': str(e)}), 400

@loaner_bp.route('/api/loaners/checkin', methods=['POST'])
@role_required('edit')
def checkin_item():
    """Check in a loaner item"""
    try:
        data = request.json
        user_name = get_user_name()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update checkout record
            query = """
            UPDATE dbo.LoanerCheckouts 
            SET checkin_date = GETDATE()
            WHERE checkout_id = ?;
            """
            
            cursor.execute(query, (data['checkout_id'],))
            
            # Log the checkin
            log_audit(cursor, 'CHECKIN', None, 'loaner_status', 'checked_out', 'available', user_name)
            
            conn.commit()
            return jsonify({'message': 'Item checked in successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error checking in item: {str(e)}")
        return jsonify({'error': str(e)}), 400

@loaner_bp.route('/api/loaners/mark-as-loaner', methods=['POST'])
@role_required('edit')
def mark_as_loaner():
    """Mark an inventory item as a loaner"""
    try:
        data = request.json
        user_name = get_user_name()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update inventory record
            query = """
            UPDATE dbo.Formatted_Company_Inventory 
            SET is_loaner = 1
            WHERE inventory_id = ?;
            """
            
            cursor.execute(query, (data['inventory_id'],))
            
            # Log the change
            log_audit(cursor, 'UPDATE', None, 'is_loaner', '0', '1', user_name)
            
            conn.commit()
            return jsonify({'message': 'Item marked as loaner successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error marking item as loaner: {str(e)}")
        return jsonify({'error': str(e)}), 400
