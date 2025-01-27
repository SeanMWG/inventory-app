-- Location Summary
WITH LocationAnalysis AS (
    SELECT 
        site_name,
        room_number,
        room_name,
        COUNT(*) as record_count,
        SUM(CASE WHEN asset_tag IS NULL OR asset_tag = '' THEN 1 ELSE 0 END) as null_asset_count,
        SUM(CASE WHEN asset_type IS NULL OR asset_type = '' THEN 1 ELSE 0 END) as null_type_count
    FROM dbo.Formatted_Company_Inventory
    GROUP BY site_name, room_number, room_name
)
SELECT 
    site_name,
    COUNT(DISTINCT room_number) as unique_rooms,
    SUM(record_count) as total_records,
    SUM(null_asset_count) as records_without_assets
FROM LocationAnalysis
GROUP BY site_name
ORDER BY site_name;
GO

-- Room Types
SELECT 'Room Type Analysis' as Analysis,
    room_name,
    COUNT(*) as count,
    SUM(CASE WHEN asset_tag IS NULL OR asset_tag = '' THEN 1 ELSE 0 END) as null_asset_count
FROM dbo.Formatted_Company_Inventory
GROUP BY room_name
ORDER BY COUNT(*) DESC;
GO

-- Asset Type Distribution
WITH AssetTypeAnalysis AS (
    SELECT 
        asset_type,
        COUNT(*) as count,
        COUNT(DISTINCT asset_tag) as unique_assets,
        SUM(CASE WHEN asset_tag IS NULL OR asset_tag = '' THEN 1 ELSE 0 END) as null_asset_count
    FROM dbo.Formatted_Company_Inventory
    WHERE asset_type IS NOT NULL AND asset_type != ''
    GROUP BY asset_type
)
SELECT 
    asset_type,
    count as total_records,
    unique_assets,
    null_asset_count,
    CASE 
        WHEN count > 0 THEN 
            CAST(ROUND(CAST(null_asset_count AS FLOAT) / count * 100, 2) AS VARCHAR) + '%'
        ELSE '0%'
    END as null_percentage
FROM AssetTypeAnalysis
WHERE count > 5  -- Show only asset types with more than 5 records
ORDER BY count DESC;
GO

-- Proposed New Structure:
/*
-- Locations table to track physical spaces
CREATE TABLE dbo.Locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,  -- Office, Storage, Server Room, etc.
    CONSTRAINT UQ_Location UNIQUE (site_name, room_number)
);

-- Equipment inventory with location reference
CREATE TABLE dbo.Equipment (
    asset_tag VARCHAR(100) PRIMARY KEY,
    location_id INT REFERENCES dbo.Locations(location_id),
    asset_type VARCHAR(100) NOT NULL,
    model VARCHAR(255),
    serial_number VARCHAR(100),
    assigned_to VARCHAR(255),
    date_assigned DATETIME2,
    date_decommissioned DATETIME2,
    is_loaner BIT NOT NULL DEFAULT 0,
    notes NVARCHAR(MAX)
);

-- Equipment loans tracking
CREATE TABLE dbo.Equipment_Loans (
    loan_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    asset_tag VARCHAR(100) NOT NULL REFERENCES dbo.Equipment(asset_tag),
    loaned_to VARCHAR(255) NOT NULL,
    checkout_date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    expected_return_date DATETIME2 NOT NULL,
    actual_return_date DATETIME2 NULL,
    checkout_notes NVARCHAR(MAX) NULL,
    return_notes NVARCHAR(MAX) NULL,
    checked_out_by VARCHAR(255) NOT NULL,
    checked_in_by VARCHAR(255) NULL
);
*/
