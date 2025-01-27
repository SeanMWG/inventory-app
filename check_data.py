import os
import pyodbc
from tabulate import tabulate

def main():
    conn = pyodbc.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    print("\nChecking for NULL or empty asset tags...")
    cursor.execute("""
        SELECT COUNT(*) as null_count
        FROM dbo.Formatted_Company_Inventory 
        WHERE asset_tag IS NULL OR asset_tag = ''
    """)
    null_count = cursor.fetchone()[0]
    print(f"Found {null_count} records with NULL or empty asset tags")
    
    if null_count > 0:
        print("\nRecords with NULL or empty asset tags:")
        cursor.execute("""
            SELECT *
            FROM dbo.Formatted_Company_Inventory 
            WHERE asset_tag IS NULL OR asset_tag = ''
        """)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        print(tabulate(rows, headers=columns, tablefmt='grid'))
    
    print("\nChecking for duplicate asset tags...")
    cursor.execute("""
        SELECT asset_tag, COUNT(*) as duplicate_count
        FROM dbo.Formatted_Company_Inventory
        WHERE asset_tag IS NOT NULL AND asset_tag != ''
        GROUP BY asset_tag
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    if duplicates:
        print("Found duplicate asset tags:")
        print(tabulate(duplicates, headers=['Asset Tag', 'Count'], tablefmt='grid'))
    else:
        print("No duplicate asset tags found")

if __name__ == '__main__':
    main()
