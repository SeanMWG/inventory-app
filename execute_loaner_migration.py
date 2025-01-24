import os
import pyodbc
from utils import get_db_connection

def read_sql_file(filename):
    """Read SQL commands from a file"""
    with open(filename, 'r') as file:
        return file.read()

def split_sql_commands(sql):
    """Split SQL script into individual commands"""
    # Split on GO statements
    commands = sql.split('\nGO\n')
    # Further split each command on semicolons, except for those within the command
    result = []
    for command in commands:
        # Remove comments and empty lines
        lines = []
        for line in command.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)
        if lines:
            result.append('\n'.join(lines))
    return result

def execute_migration():
    """Execute the loaner tables migration"""
    conn = None
    cursor = None
    try:
        # Set DATABASE_URL if not already set
        if not os.getenv('DATABASE_URL'):
            os.environ['DATABASE_URL'] = (
                'Driver={ODBC Driver 17 for SQL Server};'
                'Server=tcp:mwg-inventory-app.database.windows.net,1433;'
                'Database=mwg-inventory-app;'
                'Uid=mwg-inventory-app;'
                'Pwd=your-password-here;'
                'Encrypt=yes;'
                'TrustServerCertificate=no;'
                'Connection Timeout=30;'
            )

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        print("Starting loaner tables migration...")

        # Read and execute the migration script
        script_path = os.path.join('migration', 'create_loaner_tables.sql')
        sql = read_sql_file(script_path)
        commands = split_sql_commands(sql)

        for command in commands:
            try:
                print(f"\nExecuting command:\n{command}\n")
                cursor.execute(command)
                conn.commit()
                print("Command executed successfully")
            except Exception as e:
                print(f"Error executing command: {str(e)}")
                conn.rollback()
                raise

        print("\nVerifying migration...")

        # Verify is_loaner column
        cursor.execute("""
            SELECT 1 
            FROM sys.columns 
            WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
            AND name = 'is_loaner'
        """)
        if not cursor.fetchone():
            raise Exception("is_loaner column not found in Formatted_Company_Inventory")

        # Verify LoanerCheckouts table
        cursor.execute("""
            SELECT 1 
            FROM sys.objects 
            WHERE object_id = OBJECT_ID('dbo.LoanerCheckouts') 
            AND type = 'U'
        """)
        if not cursor.fetchone():
            raise Exception("LoanerCheckouts table not found")

        # Verify views
        for view_name in ['AvailableLoaners', 'CheckedOutLoaners']:
            cursor.execute(f"""
                SELECT 1 
                FROM sys.views 
                WHERE name = '{view_name}'
            """)
            if not cursor.fetchone():
                raise Exception(f"{view_name} view not found")

        # Verify indexes
        cursor.execute("""
            SELECT 1 
            FROM sys.indexes 
            WHERE name IN ('IX_Inventory_IsLoaner', 'IX_LoanerCheckouts_Dates')
        """)
        if len(cursor.fetchall()) != 2:
            raise Exception("Not all required indexes were created")

        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"\nError during migration: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    execute_migration()
