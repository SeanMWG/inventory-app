-- Check if notes column needs to be renamed to checkout_notes
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.LoanerCheckouts') 
    AND name = 'notes'
)
BEGIN
    EXEC sp_rename 'dbo.LoanerCheckouts.notes', 'checkout_notes', 'COLUMN';
END
GO

-- Drop and recreate views with correct column names
IF EXISTS (SELECT * FROM sys.views WHERE name = 'AvailableLoaners')
    DROP VIEW dbo.AvailableLoaners;
GO

IF EXISTS (SELECT * FROM sys.views WHERE name = 'CheckedOutLoaners')
    DROP VIEW dbo.CheckedOutLoaners;
GO

-- Create view for available loaners
CREATE VIEW dbo.AvailableLoaners AS
SELECT i.*
FROM dbo.Formatted_Company_Inventory i
LEFT JOIN dbo.LoanerCheckouts lc ON 
    i.inventory_id = lc.inventory_id AND 
    lc.checkin_date IS NULL
WHERE i.is_loaner = 1
    AND lc.checkout_id IS NULL;
GO

-- Create view for checked out loaners
CREATE VIEW dbo.CheckedOutLoaners AS
SELECT 
    i.inventory_id,
    i.site_name,
    i.room_number,
    i.room_name,
    i.asset_tag,
    i.asset_type,
    i.model,
    i.serial_number,
    i.notes as inventory_notes,
    i.assigned_to,
    i.date_assigned,
    i.date_decommissioned,
    i.location_id,
    i.is_loaner,
    lc.checkout_id,
    lc.user_name,
    lc.checkout_date,
    lc.expected_return_date,
    lc.checkout_notes
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.LoanerCheckouts lc ON i.inventory_id = lc.inventory_id
WHERE i.is_loaner = 1
    AND lc.checkin_date IS NULL;
GO

-- Verify the changes
SELECT 
    c.name as column_name,
    t.name as data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE object_id = OBJECT_ID('dbo.LoanerCheckouts')
ORDER BY c.column_id;
