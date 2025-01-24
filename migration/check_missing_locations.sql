-- Let's examine the records with missing location_ids to understand why they weren't matched
SELECT TOP 100
    site_name,
    room_number,
    room_name,
    CASE 
        WHEN site_name IS NULL AND room_number IS NULL AND room_name IS NULL THEN 'All location fields are NULL'
        ELSE 'Has some location data'
    END as reason
FROM dbo.Formatted_Company_Inventory
WHERE location_id IS NULL
ORDER BY 
    CASE 
        WHEN site_name IS NOT NULL THEN 0
        ELSE 1
    END,
    site_name,
    room_number;

-- Count of records by NULL pattern
SELECT 
    CASE 
        WHEN site_name IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END as site_name_status,
    CASE 
        WHEN room_number IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END as room_number_status,
    CASE 
        WHEN room_name IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END as room_name_status,
    COUNT(*) as record_count
FROM dbo.Formatted_Company_Inventory
WHERE location_id IS NULL
GROUP BY 
    CASE 
        WHEN site_name IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END,
    CASE 
        WHEN room_number IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END,
    CASE 
        WHEN room_name IS NULL THEN 'NULL'
        ELSE 'NOT NULL'
    END
ORDER BY record_count DESC;
