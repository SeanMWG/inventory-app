-- First add the primary key column
ALTER TABLE dbo.Formatted_Company_Inventory
ADD inventory_id INT IDENTITY(1,1);
GO

-- Make it the primary key
ALTER TABLE dbo.Formatted_Company_Inventory
ADD CONSTRAINT PK_Formatted_Company_Inventory PRIMARY KEY (inventory_id);
GO

-- Add an index on asset_tag since it's used for lookups and audit tracking
CREATE INDEX IX_Inventory_AssetTag 
ON dbo.Formatted_Company_Inventory(asset_tag);
GO

-- Verify the changes
SELECT 
    i.name as index_name,
    i.type_desc as index_type,
    i.is_primary_key,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
GROUP BY i.name, i.type_desc, i.is_primary_key;
