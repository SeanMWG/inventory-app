# Loaner Equipment Tracking Setup

This document outlines the steps to add loaner equipment tracking capabilities to the IT Hardware Inventory system.

## Overview

The changes will add:
1. A flag to mark equipment as loanable
2. A new table to track equipment loans
3. A view to easily see active loans

## Prerequisites

- Database access with ALTER permissions
- Python environment with pyodbc installed
- DATABASE_URL environment variable set

## Files

1. `add_loaner_tracking.sql`
   - Adds `is_loaner` flag to inventory table
   - Creates new `Equipment_Loans` table
   - Creates `Active_Loans` view
   - Includes safety checks and indexes

2. `apply_loaner_changes.py`
   - Safely applies database changes
   - Includes logging and error handling
   - Creates log file for tracking changes

## Installation Steps

1. Backup your database
   ```sql
   BACKUP DATABASE [YourDatabase] TO DISK = 'C:\Backups\YourDatabase.bak'
   ```

2. Review the SQL changes
   - Check `add_loaner_tracking.sql`
   - Verify table names and constraints
   - Ensure indexes are appropriate

3. Run the changes
   ```bash
   python apply_loaner_changes.py
   ```

4. Verify the changes
   ```sql
   -- Check new column
   SELECT TOP 1 * FROM dbo.Formatted_Company_Inventory;
   
   -- Check new table
   SELECT * FROM dbo.Equipment_Loans;
   
   -- Check view
   SELECT * FROM dbo.Active_Loans;
   ```

## Rollback Plan

If needed, you can rollback the changes:

```sql
-- Drop view
DROP VIEW IF EXISTS dbo.Active_Loans;

-- Drop loan tracking table
DROP TABLE IF EXISTS dbo.Equipment_Loans;

-- Remove loaner flag
ALTER TABLE dbo.Formatted_Company_Inventory
DROP COLUMN is_loaner;
```

## Monitoring

Check the `loaner_changes.log` file for:
- Execution progress
- Any errors or warnings
- Confirmation of successful changes

## Next Steps

After installation:
1. Mark appropriate equipment as loaners
2. Set up email notifications (separate configuration)
3. Train users on new loan tracking features
