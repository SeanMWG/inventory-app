-- Check if is_loaner column exists
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.Formatted_Company_Inventory') 
    AND name = 'is_loaner'
)
BEGIN
    -- Add is_loaner column if it doesn't exist
    ALTER TABLE dbo.Formatted_Company_Inventory
    ADD is_loaner BIT NOT NULL DEFAULT 0;
END
GO

-- Verify the column exists and its properties
SELECT 
    c.name as column_name,
    t.name as data_type,
    c.max_length,
    c.is_nullable,
    c.default_object_id,
    d.definition as default_value
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
LEFT JOIN sys.default_constraints d ON c.default_object_id = d.object_id
WHERE c.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
AND c.name = 'is_loaner';
