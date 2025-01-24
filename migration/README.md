# Loaner Management Migration

This directory contains the SQL scripts and Python utilities for setting up the loaner device management system.

## Database Changes

The migration adds the following to the database:

1. New column `is_loaner` (bit) to `Formatted_Company_Inventory` table
2. New table `LoanerCheckouts` for tracking device loans
3. Two views:
   - `AvailableLoaners`: Shows devices marked as loaners that aren't checked out
   - `CheckedOutLoaners`: Shows currently checked out loaner devices
4. Supporting indexes for performance

## Running the Migration

1. Set the DATABASE_URL environment variable:
```bash
# Windows CMD
set DATABASE_URL="Driver={ODBC Driver 17 for SQL Server};Server=tcp:mwg-inventory-app.database.windows.net,1433;Database=mwg-inventory-app;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Windows PowerShell
$env:DATABASE_URL="Driver={ODBC Driver 17 for SQL Server};Server=tcp:mwg-inventory-app.database.windows.net,1433;Database=mwg-inventory-app;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
```

2. Run the migration script:
```bash
python execute_loaner_migration.py
```

The script will:
- Create necessary tables and views if they don't exist
- Add required indexes
- Verify all components were created successfully

## Verifying the Migration

The migration script includes verification steps that check:
1. The `is_loaner` column exists in the inventory table
2. The `LoanerCheckouts` table exists
3. Both views are created
4. Required indexes are present

## Rollback

To rollback the changes:

```sql
-- Drop views
DROP VIEW IF EXISTS dbo.CheckedOutLoaners;
DROP VIEW IF EXISTS dbo.AvailableLoaners;

-- Drop loaner checkouts table
DROP TABLE IF EXISTS dbo.LoanerCheckouts;

-- Remove is_loaner column
ALTER TABLE dbo.Formatted_Company_Inventory
DROP COLUMN is_loaner;

-- Drop indexes
DROP INDEX IF EXISTS IX_Inventory_IsLoaner ON dbo.Formatted_Company_Inventory;
DROP INDEX IF EXISTS IX_LoanerCheckouts_Dates ON dbo.LoanerCheckouts;
```

## API Endpoints

The loaner management system adds these endpoints:

- GET `/api/loaners/available` - List available loaner devices
- GET `/api/loaners/checked-out` - List currently checked out devices
- POST `/api/loaners/checkout` - Check out a device
- POST `/api/loaners/checkin` - Check in a device

## Frontend Changes

A new loaner management interface is available at `/loaners` with:
- Tab view for available/checked-out devices
- Checkout form with user info and return date
- Device details with audit history
- Dark/light theme support
