import os
import pyodbc
from datetime import datetime

def get_db_connection():
    """Get a connection to the SQL Server database"""
    conn_str = os.getenv('DATABASE_URL')
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable is not set")
    if isinstance(conn_str, bytes):
        conn_str = conn_str.decode('utf-8')
    conn = pyodbc.connect(conn_str)
    return conn

def log_change(cursor, asset_tag, action_type, field_name, old_value, new_value, changed_by):
    """Log a change to the audit log table"""
    cursor.execute('''
        INSERT INTO dbo.AuditLog (
            asset_tag,
            changed_at,
            action_type,
            field_name,
            old_value,
            new_value,
            changed_by
        ) VALUES (?, GETDATE(), ?, ?, ?, ?, ?)
    ''', (
        asset_tag,
        action_type,
        field_name,
        str(old_value) if old_value is not None else None,
        str(new_value) if new_value is not None else None,
        changed_by
    ))
