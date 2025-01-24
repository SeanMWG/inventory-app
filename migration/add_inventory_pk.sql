-- First add the primary key column
ALTER TABLE dbo.Formatted_Company_Inventory
ADD inventory_id INT IDENTITY(1,1);
GO

-- Make it the primary key
ALTER TABLE dbo.Formatted_Company_Inventory
ADD CONSTRAINT PK_Formatted_Company_Inventory PRIMARY KEY (inventory_id);
GO

-- Verify the primary key was added
SELECT 
    i.name as index_name,
    c.name as column_name,
    i.is_primary_key
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
AND i.is_primary_key = 1;
