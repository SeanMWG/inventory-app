IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'dbo.Formatted_Company_Inventory')
    AND name = 'location_id'
)
BEGIN
    ALTER TABLE dbo.Formatted_Company_Inventory ADD
        location_id INT NULL;
END;
