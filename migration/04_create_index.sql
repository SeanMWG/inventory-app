IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IX_Inventory_LocationId'
    AND object_id = OBJECT_ID(N'dbo.Formatted_Company_Inventory')
)
BEGIN
    CREATE INDEX IX_Inventory_LocationId ON dbo.Formatted_Company_Inventory(location_id);
END;
