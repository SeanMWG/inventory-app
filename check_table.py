import os
import pyodbc

def main():
    conn = pyodbc.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("""
        SELECT 
            c.name as column_name,
            t.name as data_type,
            c.is_nullable,
            CASE WHEN pk.column_id IS NOT NULL THEN 'YES' ELSE 'NO' END as is_primary_key
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN (
            SELECT i.object_id, ic.column_id
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            WHERE i.is_primary_key = 1
        ) pk ON c.object_id = pk.object_id AND c.column_id = pk.column_id
        WHERE c.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
        ORDER BY c.column_id;
    """)
    
    print("\nTable Structure:")
    print("Column Name | Data Type | Nullable | Is Primary Key")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} | {row[1]:<10} | {row[2]:<9} | {row[3]}")

if __name__ == '__main__':
    main()
