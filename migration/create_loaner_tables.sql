-- Step 1: Add is_loaner flag to inventory table
ALTER TABLE dbo.Formatted_Company_Inventory
ADD is_loaner BIT NOT NULL DEFAULT 0;
GO

-- Step 2: Create table to track loaner checkouts
CREATE TABLE dbo.LoanerCheckouts (
    checkout_id INT IDENTITY(1,1) PRIMARY KEY,
    inventory_id INT NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    checkout_date DATETIME NOT NULL DEFAULT GETDATE(),
    expected_return_date DATETIME NULL,
    checkin_date DATETIME NULL,
    notes VARCHAR(500) NULL,
    CONSTRAINT FK_LoanerCheckouts_Inventory 
        FOREIGN KEY (inventory_id) 
        REFERENCES dbo.Formatted_Company_Inventory(id)
);
GO

-- Step 3: Create indexes for better performance
CREATE INDEX IX_LoanerCheckouts_InventoryId 
ON dbo.LoanerCheckouts(inventory_id);
GO

CREATE INDEX IX_LoanerCheckouts_Status 
ON dbo.LoanerCheckouts(checkin_date)
INCLUDE (inventory_id, user_name, checkout_date);
GO

-- Step 4: Create view for available loaners
CREATE VIEW dbo.AvailableLoaners AS
SELECT i.*
FROM dbo.Formatted_Company_Inventory i
LEFT JOIN dbo.LoanerCheckouts lc ON 
    i.id = lc.inventory_id AND 
    lc.checkin_date IS NULL
WHERE i.is_loaner = 1
    AND lc.checkout_id IS NULL;
GO

-- Step 5: Create view for checked out loaners
CREATE VIEW dbo.CheckedOutLoaners AS
SELECT 
    i.*,
    lc.checkout_id,
    lc.user_name,
    lc.checkout_date,
    lc.expected_return_date,
    lc.notes
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.LoanerCheckouts lc ON i.id = lc.inventory_id
WHERE i.is_loaner = 1
    AND lc.checkin_date IS NULL;
GO
