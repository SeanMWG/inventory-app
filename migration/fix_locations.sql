-- First, let's look at our current Locations table
SELECT * FROM dbo.Locations;

-- Then look at a sample of inventory records
SELECT TOP 100 
    site_name,
    room_number,
    room_name,
    location_id
FROM dbo.Formatted_Company_Inventory;

-- Now let's try updating the location_ids again with a simpler join
UPDATE i
SET i.location_id = l.location_id
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON 
    COALESCE(i.site_name, 'Unknown') = l.site_name AND
    COALESCE(i.room_number, 'Unknown') = l.room_number;

-- Check if that helped
SELECT COUNT(*) as total_records,
       COUNT(location_id) as records_with_location_id,
       COUNT(CASE WHEN location_id IS NULL THEN 1 END) as records_missing_location_id
FROM dbo.Formatted_Company_Inventory;
