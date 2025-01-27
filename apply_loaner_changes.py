import os
import logging
import pyodbc
import sys
import json
import traceback

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(script_dir, 'loaner_changes.log'))
    ]
)

def get_db_connection():
    """Get database connection with error handling"""
    try:
        logging.info("Attempting database connection")
        db_connection = os.getenv('DATABASE_URL', '')
        if not db_connection:
            raise Exception("DATABASE_URL environment variable is not set")
        
        # Log connection string (without password)
        safe_connection = db_connection.replace(';', '\n').split('\n')
        logging.info("Connection details:")
        for part in safe_connection:
            if not part.lower().startswith('pwd=') and not part.lower().startswith('password='):
                logging.info(f"  {part}")
        
        conn = pyodbc.connect(db_connection)
        logging.info("Database connection successful")
        return conn
    except pyodbc.Error as e:
        logging.error(f"PyODBC Error: {str(e)}")
        logging.error(f"Connection string (sanitized): {';'.join([p for p in safe_connection if not p.lower().startswith('pwd=') and not p.lower().startswith('password=')])}")
        logging.error(traceback.format_exc())
        raise
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def read_sql_file(filename):
    """Read SQL commands from file"""
    with open(filename, 'r') as file:
        return file.read()

def execute_sql_safely(cursor, sql):
    """Execute SQL commands with proper error handling"""
    try:
        # Split on GO statements (T-SQL batch separator)
        commands = sql.split('GO')
        for cmd in commands:
            if cmd.strip():  # Skip empty commands
                logging.info(f"Executing SQL command:\n{cmd.strip()}")
                cursor.execute(cmd)
                cursor.commit()
                logging.info("Command executed successfully")
    except Exception as e:
        logging.error(f"Error executing SQL: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def main():
    try:
        logging.info("Starting database updates for loaner tracking")
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read and execute SQL file
        sql_file = os.path.join(script_dir, 'add_loaner_tracking.sql')
        sql_content = read_sql_file(sql_file)
        execute_sql_safely(cursor, sql_content)
        
        logging.info("Database updates completed successfully")
        
    except Exception as e:
        logging.error(f"Failed to apply database changes: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()
