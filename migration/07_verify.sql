SELECT 
    'Location Migration Check' as check_type,
    (SELECT COUNT(DISTINCT CONCAT(ISNULL(site_name, N'Unknown'), N'-', ISNULL(room_number, N'Unknown'))) 
     FROM dbo.Formatted_Company_Inventory) as original_location_count,
    (SELECT COUNT(*) FROM dbo.Locations) as new_location_count;
