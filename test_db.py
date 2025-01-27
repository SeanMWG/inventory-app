import os
import pyodbc
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def test_connection():
    # Get database connection string
    db_connection = os.getenv('DATABASE_URL', '')
    if not db_connection:
        logging.error("DATABASE_URL environment variable is not set!")
        return

    try:
        # Log connection string (without password)
        safe_connection = db_connection.replace(';', '\n').split('\n')
        logging.info("Connection details:")
        for part in safe_connection:
            if not part.lower().startswith('pwd=') and not part.lower().startswith('password='):
                logging.info(f"  {part}")
        
        # Try to connect
        logging.info("Attempting database connection...")
        conn = pyodbc.connect(db_connection)
        logging.info("Database connection successful!")
        
        # Try a simple query
        cursor = conn.cursor()
        logging.info("Executing test query...")
        cursor.execute("SELECT COUNT(*) FROM dbo.Formatted_Company_Inventory")
        count = cursor.fetchval()
        logging.info(f"Total records: {count}")
        
        # Close connection
        conn.close()
        logging.info("Connection closed successfully")
        
    except pyodbc.Error as e:
        logging.error(f"PyODBC Error: {str(e)}")
        logging.error(f"SQL State: {e.args[0]}")
        logging.error(f"Error message: {e.args[1]}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == '__main__':
    test_connection()
