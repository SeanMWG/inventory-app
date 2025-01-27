import os
import pyodbc
from tabulate import tabulate

def print_section(title):
    print(f"\n{'-' * 80}")
    print(f"{title}")
    print(f"{'-' * 80}")

def main():
    conn = pyodbc.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    try:
        # Current Data Analysis
        print_section("Current Data Structure")
        
        # Show current table structure
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Formatted_Company_Inventory'
            ORDER BY ORDINAL_POSITION
        """)
        print("\nCurrent Table Structure:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Column', 'Type', 'Max Length', 'Nullable'], tablefmt='grid'))
        
        # Data Statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT asset_tag) as unique_assets,
                COUNT(DISTINCT site_name) as unique_sites,
                COUNT(DISTINCT room_number) as unique_rooms,
                COUNT(DISTINCT CONCAT(site_name, room_number)) as unique_locations,
                SUM(CASE WHEN asset_tag IS NULL OR asset_tag = '' THEN 1 ELSE 0 END) as null_asset_tags,
                SUM(CASE WHEN site_name IS NULL OR site_name = '' THEN 1 ELSE 0 END) as null_sites,
                SUM(CASE WHEN room_number IS NULL OR room_number = '' THEN 1 ELSE 0 END) as null_rooms
            FROM dbo.Formatted_Company_Inventory
        """)
        print("\nCurrent Data Statistics:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Total Records', 'Unique Assets', 'Unique Sites', 
                                    'Unique Rooms', 'Unique Locations', 'Null Asset Tags',
                                    'Null Sites', 'Null Rooms'], tablefmt='grid'))
        
        # Sample current data
        cursor.execute("""
            SELECT TOP 5 *
            FROM dbo.Formatted_Company_Inventory
            WHERE asset_tag IS NOT NULL AND asset_tag != ''
            ORDER BY NEWID()
        """)
        print("\nSample of Current Records:")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        print(tabulate(rows, headers=columns, tablefmt='grid'))
        
        print_section("Proposed Location Categories")
        
        # Show how locations would be categorized
        cursor.execute("""
            SELECT DISTINCT
                site_name,
                room_number,
                room_name,
                CASE 
                    WHEN room_name LIKE '%Cubicle%' THEN 'Workspace'
                    WHEN room_name LIKE '%Office%' THEN 'Workspace'
                    WHEN room_name LIKE '%Conference%' THEN 'Meeting Space'
                    WHEN room_name LIKE '%Storage%' THEN 'Storage'
                    WHEN room_name LIKE '%Server%' THEN 'IT Infrastructure'
                    WHEN room_name LIKE '%IT%' THEN 'IT Infrastructure'
                    WHEN room_name LIKE '%Restroom%' OR room_name LIKE '%Toilet%' THEN 'Facilities'
                    WHEN room_name LIKE '%Kitchen%' OR room_name LIKE '%Break%' THEN 'Common Area'
                    WHEN room_name LIKE '%Corridor%' OR room_name LIKE '%Hallway%' THEN 'Circulation'
                    ELSE 'Other'
                END as proposed_category
            FROM dbo.Formatted_Company_Inventory
            WHERE room_number IS NOT NULL
            ORDER BY site_name, room_number
        """)
        print("\nProposed Location Categorization (Sample):")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Site', 'Room', 'Room Name', 'Proposed Category'], 
                      tablefmt='grid'))
        
        print_section("Loaner Equipment Analysis")
        
        # Analyze potential loaner equipment
        cursor.execute("""
            SELECT 
                asset_type,
                asset_tag,
                site_name,
                room_number,
                room_name,
                assigned_to,
                notes
            FROM dbo.Formatted_Company_Inventory
            WHERE asset_type LIKE '%Laptop%'
                OR asset_type LIKE '%Loaner%'
                OR notes LIKE '%loaner%'
                OR notes LIKE '%temp%'
                OR notes LIKE '%temporary%'
            ORDER BY asset_type, asset_tag
        """)
        print("\nPotential Loaner Equipment:")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=['Asset Type', 'Asset Tag', 'Site', 'Room', 'Room Name',
                                    'Assigned To', 'Notes'], tablefmt='grid'))
        
        print_section("Data Preservation Summary")
        print("\nThe migration will preserve:")
        print("✓ All original location fields (site_name, room_number, room_name)")
        print("✓ All equipment details (asset_tag, asset_type, model, serial_number)")
        print("✓ All assignment information (assigned_to, date_assigned, date_decommissioned)")
        print("✓ All notes and comments")
        print("\nThe migration will add:")
        print("+ Location categorization for better organization")
        print("+ Loaner equipment tracking")
        print("+ Location history for loaned equipment")
        print("+ Audit trails for equipment changes")
        
        print_section("Validation Checks")
        
        # Check for potential data issues - split into two queries to avoid nested aggregates
        cursor.execute("""
            SELECT COUNT(*) as null_assets
            FROM dbo.Formatted_Company_Inventory
            WHERE asset_tag IS NULL OR asset_tag = ''
        """)
        null_count = cursor.fetchone()[0]

        # Get detailed information about duplicate asset tags
        cursor.execute("""
            WITH DuplicateAssets AS (
                SELECT asset_tag
                FROM dbo.Formatted_Company_Inventory
                WHERE asset_tag IS NOT NULL
                GROUP BY asset_tag
                HAVING COUNT(*) > 1
            )
            SELECT 
                i.asset_tag,
                i.site_name,
                i.room_number,
                i.room_name,
                i.asset_type,
                i.model,
                i.serial_number,
                i.assigned_to,
                i.notes
            FROM dbo.Formatted_Company_Inventory i
            INNER JOIN DuplicateAssets d ON i.asset_tag = d.asset_tag
            ORDER BY i.asset_tag, i.site_name, i.room_number
        """)
        duplicate_rows = cursor.fetchall()
        duplicate_count = len(set(row[0] for row in duplicate_rows))  # Unique duplicate asset tags

        print("\nData Quality Checks:")
        print(f"- Records with null asset tags: {null_count}")
        print(f"- Records with duplicate asset tags: {duplicate_count}")

        if duplicate_rows:
            print("\nDuplicate Asset Tag Analysis:")
            current_tag = None
            for row in duplicate_rows:
                if row[0] != current_tag:
                    current_tag = row[0]
                    print(f"\nAsset Tag: {current_tag}")
                print(f"  Location: {row[1]} {row[2]} ({row[3]})")
                print(f"  Type: {row[4]}, Model: {row[5]}, SN: {row[6]}")
                print(f"  Assigned To: {row[7]}")
                if row[8]:  # Notes
                    print(f"  Notes: {row[8]}")
        
        if null_count > 0 or duplicate_count > 0:
            print("\nRECOMMENDATION: Address data quality issues before migration:")
            print("1. Assign valid asset tags to equipment without tags")
            print("2. Resolve duplicate asset tags")
            print("3. Consider creating a separate table for tracking spaces/rooms")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
