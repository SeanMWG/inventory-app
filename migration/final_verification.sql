-- Let's do a final verification of our migration

-- 1. Check that all inventory records have a location_id
SELECT COUNT(*) as total_records,
       COUNT(location_id) as records_with_location_id,
       COUNT(CASE WHEN location_id IS NULL THEN 1 END) as records_missing_location_id
FROM dbo.Formatted_Company_Inventory;

-- 2. Check the distribution of locations
SELECT 
    l.site_name,
    l.room_type,
    COUNT(*) as equipment_count
FROM dbo.Locations l
LEFT JOIN dbo.Formatted_Company_Inventory i ON l.location_id = i.location_id
GROUP BY l.site_name, l.room_type
ORDER BY l.site_name, l.room_type;

-- 3. Verify foreign key constraint is working
-- This should fail if the constraint is working properly
-- (commented out for safety - uncomment to test)
/*
INSERT INTO dbo.Formatted_Company_Inventory (location_id)
VALUES (99999);  -- This should fail because this location_id doesn't exist
*/
