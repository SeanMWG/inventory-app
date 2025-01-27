-- Step 1: Create Locations table
CREATE TABLE dbo.Locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    CONSTRAINT UQ_Location UNIQUE (site_name, room_number)
);

-- Step 2: Populate Locations table from existing data
INSERT INTO dbo.Locations (site_name, room_number, room_name, room_type)
SELECT DISTINCT 
    ISNULL(site_name, N'Unknown') as site_name,
    ISNULL(room_number, N'Unknown') as room_number,
    ISNULL(room_name, N'Unknown') as room_name,
    CASE 
        WHEN room_name LIKE N'%Cubicle%' THEN N'Cubicle'
        WHEN room_name LIKE N'%Office%' THEN N'Office'
        WHEN room_name LIKE N'%Storage%' THEN N'Storage'
        WHEN room_name LIKE N'%Server%' THEN N'Server Room'
        ELSE N'Other'
    END as room_type
FROM dbo.Formatted_Company_Inventory
WHERE site_name IS NOT NULL 
   OR room_number IS NOT NULL 
   OR room_name IS NOT NULL;

-- Step 3: Add location_id to Equipment table
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'dbo.Equipment')
    AND name = 'location_id'
)
BEGIN
    ALTER TABLE dbo.Equipment ADD
        location_id INT NULL;
END;

-- Step 4: Create index for faster joins
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'IX_Equipment_LocationId'
    AND object_id = OBJECT_ID(N'dbo.Equipment')
)
BEGIN
    CREATE INDEX IX_Equipment_LocationId ON dbo.Equipment(location_id);
END;

-- Step 5: Update Equipment with location_id values
UPDATE e
SET e.location_id = l.location_id
FROM dbo.Equipment e
JOIN dbo.Formatted_Company_Inventory i ON e.asset_tag = i.asset_tag
JOIN dbo.Locations l ON 
    ISNULL(i.site_name, N'Unknown') = l.site_name AND
    ISNULL(i.room_number, N'Unknown') = l.room_number;

-- Step 6: Add foreign key constraint after data is migrated
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys 
    WHERE name = 'FK_Equipment_Location'
)
BEGIN
    ALTER TABLE dbo.Equipment 
    ADD CONSTRAINT FK_Equipment_Location 
    FOREIGN KEY (location_id) REFERENCES dbo.Locations(location_id);
END;

-- Verification Queries
-- Check if all locations were migrated
SELECT 
    'Location Migration Check' as check_type,
    (SELECT COUNT(DISTINCT CONCAT(ISNULL(site_name, N'Unknown'), N'-', ISNULL(room_number, N'Unknown'))) 
     FROM dbo.Formatted_Company_Inventory) as original_location_count,
    (SELECT COUNT(*) FROM dbo.Locations) as new_location_count;

-- Check if all equipment records have location_id
SELECT 
    'Equipment Location Check' as check_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) as missing_location
FROM dbo.Equipment;

-- Sample joined data to verify relationships
SELECT TOP 5
    e.asset_tag,
    l.site_name,
    l.room_number,
    l.room_name,
    l.room_type
FROM dbo.Equipment e
LEFT JOIN dbo.Locations l ON e.location_id = l.location_id;
