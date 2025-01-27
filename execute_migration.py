import pyodbc
import os
from datetime import datetime

# Database connection string
conn_str = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:inventory-sql-server-sean.database.windows.net,1433;Database=inventory-db;Uid=sqladmin;Pwd=xK9#mP2$vL5nQ8@jR3;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

class SQLBuilder:
    @staticmethod
    def create_table(table_name, columns, constraints=None):
        cols = []
        for name, spec in columns:
            cols.append(f"    {name} {spec}")
        if constraints:
            for c in constraints:
                cols.append(f"    {c}")
        return f"CREATE TABLE {table_name} (\n" + ",\n".join(cols) + "\n)"

    @staticmethod
    def insert_select(table, columns, select_stmt):
        return (
            f"INSERT INTO {table} ({', '.join(columns)})\n"
            f"{select_stmt}"
        )

    @staticmethod
    def if_not_exists(condition, action):
        return (
            "IF NOT EXISTS (\n"
            f"    {condition}\n"
            ")\n"
            "BEGIN\n"
            f"    {action}\n"
            "END"
        )

    @staticmethod
    def update_join(table, alias, set_clause, join_table, join_alias, join_conditions):
        return (
            f"UPDATE {alias}\n"
            f"SET {set_clause}\n"
            f"FROM {table} {alias}\n"
            f"JOIN {join_table} {join_alias} ON\n"
            f"    {' AND '.join(join_conditions)}"
        )

def get_migration_steps():
    # Step 1: Create Locations table
    create_table = SQLBuilder.create_table(
        "dbo.Locations",
        [
            ("location_id", "INT IDENTITY(1,1) PRIMARY KEY"),
            ("site_name", "VARCHAR(100) NOT NULL"),
            ("room_number", "VARCHAR(50) NOT NULL"),
            ("room_name", "VARCHAR(100) NOT NULL"),
            ("room_type", "VARCHAR(50) NOT NULL")
        ],
        ["CONSTRAINT UQ_Location UNIQUE (site_name, room_number)"]
    )

    # Step 2: Populate Locations table
    select_stmt = """SELECT DISTINCT 
    ISNULL(site_name, N'Unknown'),
    ISNULL(room_number, N'Unknown'),
    ISNULL(room_name, N'Unknown'),
    CASE 
        WHEN room_name LIKE N'%Cubicle%' THEN N'Cubicle'
        WHEN room_name LIKE N'%Office%' THEN N'Office'
        WHEN room_name LIKE N'%Storage%' THEN N'Storage'
        WHEN room_name LIKE N'%Server%' THEN N'Server Room'
        ELSE N'Other'
    END
FROM dbo.Formatted_Company_Inventory
WHERE site_name IS NOT NULL 
   OR room_number IS NOT NULL 
   OR room_name IS NOT NULL"""
    populate_table = SQLBuilder.insert_select(
        "dbo.Locations",
        ["site_name", "room_number", "room_name", "room_type"],
        select_stmt
    )

    # Step 3: Add location_id to Equipment
    add_column = SQLBuilder.if_not_exists(
        "SELECT 1 FROM sys.columns\nWHERE object_id = OBJECT_ID(N'dbo.Formatted_Company_Inventory')\nAND name = 'location_id'",
        "ALTER TABLE dbo.Formatted_Company_Inventory ADD location_id INT NULL"
    )

    # Step 4: Create index
    create_index = SQLBuilder.if_not_exists(
        "SELECT 1 FROM sys.indexes\nWHERE name = 'IX_Inventory_LocationId'\nAND object_id = OBJECT_ID(N'dbo.Formatted_Company_Inventory')",
        "CREATE INDEX IX_Inventory_LocationId ON dbo.Formatted_Company_Inventory(location_id)"
    )

    # Step 5: Update location_id values
    update_ids = SQLBuilder.update_join(
        "dbo.Formatted_Company_Inventory", "i",
        "i.location_id = l.location_id",
        "dbo.Locations", "l",
        [
            "ISNULL(i.site_name, N'Unknown') = l.site_name",
            "ISNULL(i.room_number, N'Unknown') = l.room_number"
        ]
    )

    # Step 6: Add foreign key constraint
    add_fk = SQLBuilder.if_not_exists(
        "SELECT 1 FROM sys.foreign_keys\nWHERE name = 'FK_Inventory_Location'",
        "ALTER TABLE dbo.Formatted_Company_Inventory\nADD CONSTRAINT FK_Inventory_Location\nFOREIGN KEY (location_id) REFERENCES dbo.Locations(location_id)"
    )

    return [
        ("Create Locations table", create_table),
        ("Populate Locations table", populate_table),
        ("Add location_id to Inventory", add_column),
        ("Create index", create_index),
        ("Update location_id values", update_ids),
        ("Add foreign key constraint", add_fk)
    ]

def execute_sql(cursor, sql, step_name, dry_run=True):
    """Execute SQL with proper error handling"""
    print(f"\nExecuting: {step_name}")
    
    if dry_run:
        print("\nDRY RUN - SQL to execute:")
        print("=" * 80)
        print(sql)
        print("=" * 80)
        return True
    
    try:
        cursor.execute(sql)
        return True
    except Exception as e:
        print(f"Error in {step_name}: {str(e)}")
        return False

def backup_table(cursor, table_name, dry_run=True):
    """Create backup of table before migration"""
    backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    sql = f"SELECT * INTO {backup_name} FROM {table_name}"
    
    if dry_run:
        print(f"\nWould create backup: {backup_name}")
        return True
    
    try:
        cursor.execute(sql)
        print(f"Created backup: {backup_name}")
        return True
    except Exception as e:
        print(f"Backup error for {table_name}: {str(e)}")
        return False

def main(dry_run=True):
    """Main migration function"""
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        if not dry_run:
            print("\nCreating backups...")
            tables_to_backup = ['Formatted_Company_Inventory']
            for table in tables_to_backup:
                if not backup_table(cursor, table, dry_run):
                    print("Backup failed, aborting migration")
                    return False
        
        # Execute each step
        for step_name, sql in get_migration_steps():
            if not execute_sql(cursor, sql, step_name, dry_run):
                print(f"\nStep '{step_name}' failed, rolling back...")
                if not dry_run:
                    conn.rollback()
                return False
        
        if not dry_run:
            # Run verification queries
            verify_sql = """SELECT 
    'Location Migration Check' as check_type,
    (SELECT COUNT(DISTINCT CONCAT(ISNULL(site_name, N'Unknown'), N'-', ISNULL(room_number, N'Unknown'))) 
     FROM dbo.Formatted_Company_Inventory) as original_location_count,
    (SELECT COUNT(*) FROM dbo.Locations) as new_location_count"""
            print("\nVerification Results:")
            print("=" * 80)
            cursor.execute(verify_sql)
            row = cursor.fetchone()
            print(f"Original locations: {row[1]}")
            print(f"New locations: {row[2]}")
            print("=" * 80)
            
            conn.commit()
            print("\nMigration completed successfully!")
        else:
            print("\nDry run completed successfully. No changes were made to the database.")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if not dry_run:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # First do a dry run
    print("Starting dry run to validate migration steps...")
    if main(dry_run=True):
        response = input("\nDry run successful. Would you like to proceed with the actual migration? (yes/no): ")
        if response.lower() == 'yes':
            print("\nExecuting actual migration...")
            main(dry_run=False)
        else:
            print("Migration cancelled.")
    else:
        print("Dry run failed. Please fix the issues before proceeding with actual migration.")
