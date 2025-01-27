import os
import pyodbc
from tabulate import tabulate

def main():
    conn = pyodbc.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    with open('analyze_structure.sql', 'r') as file:
        script = file.read()
    
    # Split the script on GO statements if present
    statements = script.split('GO')
    
    try:
        for statement in statements:
            if statement.strip():
                # Execute each statement
                cursor.execute(statement)
                
                # Fetch and display results if any
                try:
                    while True:
                        rows = cursor.fetchall()
                        if not rows:
                            break
                            
                        # Get column names
                        columns = [column[0] for column in cursor.description]
                        
                        # Print results in table format
                        print("\nResults:")
                        print(tabulate(rows, headers=columns, tablefmt='grid'))
                        
                        # Try to move to next result set
                        if not cursor.nextset():
                            break
                            
                except pyodbc.ProgrammingError:
                    # No results to fetch
                    pass
                    
    except Exception as e:
        print(f"Error executing SQL: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
