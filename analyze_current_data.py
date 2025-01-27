import pyodbc
import json
from datetime import datetime

# Database connection string using Driver 17
conn_str = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:inventory-sql-server-sean.database.windows.net,1433;Database=inventory-db;Uid=sqladmin;Pwd=xK9#mP2$vL5nQ8@jR3;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(f"Object of type {type(x)} is not JSON serializable")

try:
    # Connect to the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("\nConnected to database successfully")
    
    # Get total count of records
    cursor.execute("SELECT COUNT(*) FROM dbo.Formatted_Company_Inventory")
    total_records = cursor.fetchone()[0]
    print(f"\nTotal records: {total_records}")
    
    # Location Analysis
    print("\nLocation Analysis:")
    cursor.execute("""
        SELECT 
            site_name,
            COUNT(DISTINCT room_number) as unique_rooms,
            COUNT(*) as total_records
        FROM dbo.Formatted_Company_Inventory
        GROUP BY site_name
        ORDER BY site_name
    """)
    
    for row in cursor.fetchall():
        print(f"  Site: {row[0]}")
        print(f"    - Unique rooms: {row[1]}")
        print(f"    - Total records: {row[2]}")
    
    # Room Type Analysis
    print("\nTop Room Types:")
    cursor.execute("""
        SELECT 
            room_name,
            COUNT(*) as count
        FROM dbo.Formatted_Company_Inventory
        GROUP BY room_name
        ORDER BY COUNT(*) DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} items")
    
    # Asset Type Distribution
    print("\nTop Asset Types:")
    cursor.execute("""
        SELECT 
            asset_type,
            COUNT(*) as count,
            COUNT(DISTINCT asset_tag) as unique_assets
        FROM dbo.Formatted_Company_Inventory
        WHERE asset_type IS NOT NULL AND asset_type != ''
        GROUP BY asset_type
        ORDER BY COUNT(*) DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}")
        print(f"    - Total records: {row[1]}")
        print(f"    - Unique assets: {row[2]}")
    
    print("\nThis analysis shows we could benefit from a separate Locations table that would:")
    print("1. Standardize site names and room numbers")
    print("2. Allow better tracking of space utilization")
    print("3. Enable hierarchical location management")
    print("\nProposed structure would be:")
    print("""
    CREATE TABLE dbo.Locations (
        location_id INT IDENTITY(1,1) PRIMARY KEY,
        site_name VARCHAR(100) NOT NULL,
        room_number VARCHAR(50) NOT NULL,
        room_name VARCHAR(100) NOT NULL,
        room_type VARCHAR(50) NOT NULL,
        CONSTRAINT UQ_Location UNIQUE (site_name, room_number)
    );
    
    -- Then modify Equipment table to reference locations
    ALTER TABLE dbo.Equipment ADD
        location_id INT REFERENCES dbo.Locations(location_id);
    """)

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    if 'conn' in locals():
        conn.close()
        print("\nDatabase connection closed")
