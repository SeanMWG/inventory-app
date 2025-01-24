-- Let's verify everything is working correctly

-- 1. Check location assignments
SELECT TOP 100
    i.site_name,
    i.room_number,
    i.room_name,
    l.location_id,
    l.room_type
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON i.location_id = l.location_id
ORDER BY l.site_name, l.room_number;

-- 2. Check location distribution
SELECT 
    l.site_name,
    l.room_type,
    COUNT(*) as equipment_count
FROM dbo.Locations l
JOIN dbo.Formatted_Company_Inventory i ON l.location_id = i.location_id
GROUP BY l.site_name, l.room_type
ORDER BY l.site_name, l.room_type;

-- 3. Verify constraints are in place
SELECT 
    fk.name as constraint_name,
    OBJECT_NAME(fk.parent_object_id) as table_name,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) as column_name,
    OBJECT_NAME(fk.referenced_object_id) as referenced_table_name,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) as referenced_column_name
FROM sys.foreign_keys fk
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE fk.name = 'FK_Inventory_Location';
