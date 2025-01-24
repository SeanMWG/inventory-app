# Loaner Management Feature Migration

This migration adds loaner tracking functionality to the inventory system.

## Database Changes

1. Added `is_loaner` flag to inventory table
2. Created `LoanerCheckouts` table for tracking checkouts
3. Created views for querying available and checked-out items:
   - `AvailableLoaners`
   - `CheckedOutLoaners`

## Files Changed

- `app.py`: Added loaner routes blueprint and new endpoint
- `templates/index.html`: Added navigation to loaner management
- `templates/loaner_management.html`: New UI for managing loaners
- `routes/loaner_routes.py`: New API endpoints for loaner operations
- `migration/*.sql`: Database migration scripts

## Migration Order

1. Run database scripts in order:
   ```sql
   -- Add is_loaner flag and create tables
   step1_create_locations.sql
   step2_populate_locations.sql
   step3_add_location_id.sql
   step4_add_foreign_key.sql
   ```

2. Deploy application changes:
   - Copy new files to server
   - Update existing files
   - Restart application

## Rollback Plan

If issues occur:
1. Drop new views
2. Drop LoanerCheckouts table
3. Remove is_loaner column
4. Revert application code changes
