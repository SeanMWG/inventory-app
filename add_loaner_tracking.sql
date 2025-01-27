-- Add loaner tracking capability
SET NOCOUNT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    -- Step 1: Check for NULL values in asset_tag
    DECLARE @NullCount int;
    SELECT @NullCount = COUNT(*) 
    FROM dbo.Formatted_Company_Inventory 
    WHERE asset_tag IS NULL OR asset_tag = '';

    IF @NullCount > 0
    BEGIN
        ROLLBACK;
        RAISERROR ('Cannot proceed: Found %d records with NULL or empty asset_tag values. Please update these records first.', 16, 1, @NullCount);
        RETURN;
    END;

    -- Step 2: Check for duplicates
    DECLARE @DuplicateCount int;
    SELECT @DuplicateCount = COUNT(*) 
    FROM (
        SELECT asset_tag
        FROM dbo.Formatted_Company_Inventory
        WHERE asset_tag IS NOT NULL
        GROUP BY asset_tag
        HAVING COUNT(*) > 1
    ) AS Duplicates;

    IF @DuplicateCount > 0
    BEGIN
        ROLLBACK;
        RAISERROR ('Cannot proceed: Found %d duplicate asset_tag values. Please fix duplicates first.', 16, 1, @DuplicateCount);
        RETURN;
    END;

    -- Step 3: Add primary key constraint to asset_tag if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM sys.indexes 
        WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
        AND name = 'PK_Formatted_Company_Inventory'
    )
    BEGIN
        -- Make it NOT NULL first
        ALTER TABLE dbo.Formatted_Company_Inventory
        ALTER COLUMN asset_tag VARCHAR(100) NOT NULL;
        
        -- Then add the primary key
        ALTER TABLE dbo.Formatted_Company_Inventory
        ADD CONSTRAINT PK_Formatted_Company_Inventory PRIMARY KEY (asset_tag);
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;
    THROW;
END CATCH;

-- Step 4: Add is_loaner flag in a separate transaction
BEGIN TRY
    BEGIN TRANSACTION;

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

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;
    THROW;
END CATCH;

-- Step 5: Create equipment loans table in a separate transaction
BEGIN TRY
    BEGIN TRANSACTION;

    IF NOT EXISTS (
        SELECT 1 
        FROM sys.objects 
        WHERE object_id = OBJECT_ID('dbo.Equipment_Loans')
        AND type = 'U'
    )
    BEGIN
        CREATE TABLE dbo.Equipment_Loans (
            loan_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            asset_tag VARCHAR(100) NOT NULL,
            loaned_to VARCHAR(255) NOT NULL,
            checkout_date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            expected_return_date DATETIME2 NOT NULL,
            actual_return_date DATETIME2 NULL,
            checkout_notes NVARCHAR(MAX) NULL,
            return_notes NVARCHAR(MAX) NULL,
            checked_out_by VARCHAR(255) NOT NULL,
            checked_in_by VARCHAR(255) NULL,
            CONSTRAINT FK_EquipmentLoans_Inventory 
                FOREIGN KEY (asset_tag) 
                REFERENCES dbo.Formatted_Company_Inventory(asset_tag)
                ON DELETE NO ACTION
                ON UPDATE NO ACTION
        );

        -- Add indexes for performance
        CREATE INDEX IX_EquipmentLoans_AssetTag 
        ON dbo.Equipment_Loans(asset_tag);

        CREATE INDEX IX_EquipmentLoans_Status 
        ON dbo.Equipment_Loans(actual_return_date)
        INCLUDE (asset_tag, expected_return_date);
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;
    THROW;
END CATCH;

-- Step 6: Create view in a separate transaction
BEGIN TRY
    BEGIN TRANSACTION;

    IF EXISTS (
        SELECT 1 
        FROM sys.views 
        WHERE object_id = OBJECT_ID('dbo.Active_Loans')
    )
    BEGIN
        DROP VIEW dbo.Active_Loans;
    END;

    EXEC('CREATE VIEW dbo.Active_Loans AS
    SELECT 
        l.loan_id,
        l.asset_tag,
        i.asset_type,
        i.model,
        i.serial_number,
        l.loaned_to,
        l.checkout_date,
        l.expected_return_date,
        l.checkout_notes,
        l.checked_out_by,
        CASE 
            WHEN l.expected_return_date < GETUTCDATE() THEN 1 
            ELSE 0 
        END as is_overdue
    FROM dbo.Equipment_Loans l
    JOIN dbo.Formatted_Company_Inventory i ON l.asset_tag = i.asset_tag
    WHERE l.actual_return_date IS NULL;');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;
    THROW;
END CATCH;
