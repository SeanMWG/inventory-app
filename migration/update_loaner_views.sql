-- Drop existing views if they exist
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
    lc.notes as checkout_notes
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.LoanerCheckouts lc ON i.inventory_id = lc.inventory_id
WHERE i.is_loaner = 1
    AND lc.checkin_date IS NULL;
GO
