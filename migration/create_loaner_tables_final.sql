-- Create table to track loaner checkouts
CREATE TABLE dbo.LoanerCheckouts (
    checkout_id INT IDENTITY(1,1) PRIMARY KEY,
    inventory_id INT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    checkout_date DATETIME NOT NULL DEFAULT GETDATE(),
    expected_return_date DATETIME NULL,
    checkin_date DATETIME NULL,
    checkout_notes VARCHAR(500) NULL,
    CONSTRAINT FK_LoanerCheckouts_Inventory 
        FOREIGN KEY (inventory_id) 
        REFERENCES dbo.Formatted_Company_Inventory(inventory_id)
);
GO

-- Create indexes for better performance
CREATE INDEX IX_LoanerCheckouts_InventoryId 
ON dbo.LoanerCheckouts(inventory_id);
GO

CREATE INDEX IX_LoanerCheckouts_Status 
ON dbo.LoanerCheckouts(checkin_date)
INCLUDE (inventory_id, user_name, checkout_date);
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
