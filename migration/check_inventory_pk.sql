-- Check existing primary key and indexes
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

-- Check if asset_tag has an index
SELECT 
    i.name as index_name,
    c.name as column_name,
    i.is_unique,
    i.is_primary_key
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.Formatted_Company_Inventory')
AND c.name = 'asset_tag';
