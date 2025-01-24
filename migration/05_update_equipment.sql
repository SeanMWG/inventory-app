UPDATE i
SET i.location_id = l.location_id
FROM dbo.Formatted_Company_Inventory i
JOIN dbo.Locations l ON 
    ISNULL(i.site_name, N'Unknown') = l.site_name AND
    ISNULL(i.room_number, N'Unknown') = l.room_number;
