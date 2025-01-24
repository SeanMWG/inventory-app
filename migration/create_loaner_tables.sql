-- Create loaner flag in main inventory table
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
    AND name = 'is_loaner'
)
BEGIN
    ALTER TABLE dbo.Formatted_Company_Inventory
    ADD is_loaner BIT NOT NULL DEFAULT 0;
END;

-- Create loaner checkouts table
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID('dbo.LoanerCheckouts') AND type = 'U')
BEGIN
    CREATE TABLE dbo.LoanerCheckouts (
        checkout_id INT IDENTITY(1,1) PRIMARY KEY,
        inventory_id INT NOT NULL,
        user_name NVARCHAR(255) NOT NULL,
        checkout_date DATETIME NOT NULL DEFAULT GETDATE(),
        expected_return_date DATETIME,
        checkin_date DATETIME,
        checkout_notes NVARCHAR(MAX),
        CONSTRAINT FK_LoanerCheckouts_Inventory 
            FOREIGN KEY (inventory_id) 
            REFERENCES dbo.Formatted_Company_Inventory (inventory_id)
    );
END;

-- Create view for available loaners
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'AvailableLoaners')
    DROP VIEW dbo.AvailableLoaners;
GO

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
IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'CheckedOutLoaners')
    DROP VIEW dbo.CheckedOutLoaners;
GO

CREATE VIEW dbo.CheckedOutLoaners AS
SELECT 
    i.*,
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

-- Create index on is_loaner flag
IF NOT EXISTS (
    SELECT 1 
    FROM sys.indexes 
    WHERE name = 'IX_Inventory_IsLoaner' 
    AND object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
)
BEGIN
    CREATE INDEX IX_Inventory_IsLoaner 
    ON dbo.Formatted_Company_Inventory (is_loaner)
    INCLUDE (inventory_id, asset_tag, asset_type, model, serial_number);
END;

-- Create index on checkout dates
IF NOT EXISTS (
    SELECT 1 
    FROM sys.indexes 
    WHERE name = 'IX_LoanerCheckouts_Dates' 
    AND object_id = OBJECT_ID('dbo.LoanerCheckouts')
)
BEGIN
    CREATE INDEX IX_LoanerCheckouts_Dates 
    ON dbo.LoanerCheckouts (checkout_date, checkin_date, expected_return_date)
    INCLUDE (inventory_id, user_name);
END;
