import pyodbc

# Database connection string
conn_str = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:inventory-sql-server-sean.database.windows.net,1433;Database=inventory-db;Uid=sqladmin;Pwd=xK9#mP2$vL5nQ8@jR3;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

try:
    # Connect to the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("\nChecking database structure...")
    
    # Check tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    print("\nExisting tables:")
    tables = cursor.fetchall()
    for table in tables:
        print(f"\nTable: {table[0]}")
        
        # Get column information
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table[0]}'
            ORDER BY ORDINAL_POSITION
        """)
        
        print("Columns:")
        for col in cursor.fetchall():
            nullable = "NULL" if col[3] == 'YES' else "NOT NULL"
            length = f"({col[2]})" if col[2] is not None else ""
            print(f"  - {col[0]}: {col[1]}{length} {nullable}")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
        print("\nDatabase connection closed")
