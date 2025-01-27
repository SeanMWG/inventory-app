import pyodbc
import sys

def list_drivers():
    print("Available ODBC drivers:")
    for driver in pyodbc.drivers():
        print(f"  - {driver}")

def check_sql_server_driver():
    drivers = pyodbc.drivers()
    required_driver = "ODBC Driver 18 for SQL Server"
    
    if required_driver in drivers:
        print(f"\n✓ {required_driver} is installed")
        return True
    else:
        print(f"\n✗ {required_driver} is not installed")
        print("\nTo fix this:")
        print("1. Download the driver from Microsoft:")
        print("   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
        print("2. Run the installer")
        print("3. Restart your terminal/IDE after installation")
        return False

if __name__ == "__main__":
    list_drivers()
    sys.exit(0 if check_sql_server_driver() else 1)
