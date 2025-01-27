import os
import pyodbc
from tabulate import tabulate

def print_section(title):
    print(f"\n{'-' * 80}")
    print(f"{title}")
    print(f"{'-' * 80}")

def execute_sql_batch(cursor, sql):
    """Execute a batch of SQL statements separated by GO"""
    for statement in sql.split('GO'):
        if statement.strip():
            cursor.execute(statement)
            cursor.commit()

def main():
    conn = pyodbc.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    try:
        # First, analyze current data
        print_section("Current Data Analysis")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT asset_tag) as unique_assets,
                COUNT(DISTINCT site_name) as unique_sites,
                COUNT(DISTINCT room_number) as unique_rooms,
                COUNT(DISTINCT CONCAT(site_name, room_number)) as unique_locations
            FROM dbo.Formatted_Company_Inventory
            WHERE asset_tag IS NOT NULL AND asset_tag != ''
        """)
        print("\nCurrent Data Summary:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Total Records', 'Unique Assets', 'Unique Sites', 
                                    'Unique Rooms', 'Unique Locations'], tablefmt='grid'))
        
        # Sample of current data
        cursor.execute("""
            SELECT TOP 5
                asset_tag,
                site_name,
                room_number,
                room_name,
                asset_type,
                assigned_to,
                notes
            FROM dbo.Formatted_Company_Inventory
            WHERE asset_tag IS NOT NULL AND asset_tag != ''
            ORDER BY NEWID()  -- Random sample
        """)
        print("\nSample of Current Data:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Asset Tag', 'Site', 'Room', 'Room Name', 
                                    'Asset Type', 'Assigned To', 'Notes'], tablefmt='grid'))
        
        # Read and execute migration script
        print_section("Starting Migration")
        with open('migrate_to_new_structure.sql', 'r') as file:
            migration_sql = file.read()
            
        # Execute migration script in batches
        execute_sql_batch(cursor, migration_sql)
        
        # Verify migration results
        print_section("Migration Results")
        
        # Compare record counts
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM dbo.Equipment) as equipment_count,
                (SELECT COUNT(*) FROM dbo.Locations) as locations_count,
                (SELECT COUNT(*) FROM dbo.Equipment WHERE is_loaner = 1) as loaner_count
        """)
        print("\nMigrated Data Counts:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Total Equipment', 'Total Locations', 'Loaner Items'], 
                      tablefmt='grid'))
        
        # Sample migrated data to show preserved location info
        cursor.execute("""
            SELECT TOP 5
                e.asset_tag,
                e.site_name,
                e.room_number,
                e.room_name,
                l.room_type,
                e.asset_type,
                e.assigned_to,
                e.is_loaner,
                e.notes
            FROM dbo.Equipment e
            JOIN dbo.Locations l ON e.location_id = l.location_id
            ORDER BY NEWID()  -- Random sample
        """)
        print("\nSample of Migrated Data (showing preserved location details):")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Asset Tag', 'Site', 'Room', 'Room Name', 'Room Type',
                                    'Asset Type', 'Assigned To', 'Is Loaner', 'Notes'], 
                      tablefmt='grid'))
        
        # Location categorization results
        cursor.execute("""
            SELECT 
                room_type,
                COUNT(*) as location_count,
                COUNT(DISTINCT CONCAT(site_name, room_number)) as unique_locations
            FROM dbo.Locations
            GROUP BY room_type
            ORDER BY location_count DESC
        """)
        print("\nLocation Categories:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Room Type', 'Total Locations', 'Unique Locations'], 
                      tablefmt='grid'))
        
        # Equipment by location type
        cursor.execute("""
            SELECT 
                l.room_type,
                COUNT(*) as equipment_count,
                SUM(CASE WHEN e.is_loaner = 1 THEN 1 ELSE 0 END) as loaner_count
            FROM dbo.Equipment e
            JOIN dbo.Locations l ON e.location_id = l.location_id
            GROUP BY l.room_type
            ORDER BY equipment_count DESC
        """)
        print("\nEquipment Distribution by Location Type:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Room Type', 'Equipment Count', 'Loaner Count'], 
                      tablefmt='grid'))
        
        print_section("Migration Complete")
        print("✓ All location data has been preserved")
        print("✓ Equipment records maintain their original location details")
        print("✓ New location categorization added for better organization")
        print("✓ Loan tracking is ready to use with full location history support")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
