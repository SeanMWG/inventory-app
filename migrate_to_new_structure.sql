-- Step 1: Create new tables
BEGIN TRANSACTION;

-- Create Locations table and migrate location data
CREATE TABLE dbo.Locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,  -- Office, Storage, Server Room, etc.
    CONSTRAINT UQ_Location UNIQUE (site_name, room_number)
);

-- Insert distinct locations, categorizing room types
INSERT INTO dbo.Locations (site_name, room_number, room_name, room_type)
SELECT DISTINCT 
    COALESCE(site_name, 'Unknown') as site_name,
    COALESCE(room_number, 'Unknown') as room_number,
    COALESCE(room_name, 'Unknown') as room_name,
    CASE 
        WHEN room_name LIKE '%Cubicle%' THEN 'Workspace'
        WHEN room_name LIKE '%Office%' THEN 'Workspace'
        WHEN room_name LIKE '%Conference%' THEN 'Meeting Space'
        WHEN room_name LIKE '%Storage%' THEN 'Storage'
        WHEN room_name LIKE '%Server%' THEN 'IT Infrastructure'
        WHEN room_name LIKE '%IT%' THEN 'IT Infrastructure'
        WHEN room_name LIKE '%Restroom%' OR room_name LIKE '%Toilet%' THEN 'Facilities'
        WHEN room_name LIKE '%Kitchen%' OR room_name LIKE '%Break%' THEN 'Common Area'
        WHEN room_name LIKE '%Corridor%' OR room_name LIKE '%Hallway%' THEN 'Circulation'
        ELSE 'Other'
    END as room_type
FROM dbo.Formatted_Company_Inventory
WHERE room_number IS NOT NULL;

COMMIT;
GO

-- Step 2: Create Equipment table
BEGIN TRANSACTION;

CREATE TABLE dbo.Equipment (
    asset_tag VARCHAR(100) PRIMARY KEY,
    -- Preserve original location fields
    site_name VARCHAR(100),
    room_number VARCHAR(50),
    room_name VARCHAR(100),
    -- Add location reference for hierarchical queries
    location_id INT REFERENCES dbo.Locations(location_id),
    -- Equipment details
    asset_type VARCHAR(100) NOT NULL,
    model VARCHAR(255),
    serial_number VARCHAR(100),
    assigned_to VARCHAR(255),
    date_assigned DATETIME2,
    date_decommissioned DATETIME2,
    is_loaner BIT NOT NULL DEFAULT 0,
    notes NVARCHAR(MAX),
    -- Add audit fields
    last_updated DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    last_updated_by VARCHAR(100)
);

-- Migrate equipment data, setting is_loaner flag
INSERT INTO dbo.Equipment (
    asset_tag,
    site_name,
    room_number,
    room_name,
    location_id,
    asset_type,
    model,
    serial_number,
    assigned_to,
    date_assigned,
    date_decommissioned,
    is_loaner,
    notes,
    last_updated_by
)
SELECT 
    i.asset_tag,
    i.site_name,
    i.room_number,
    i.room_name,
    l.location_id,
    CASE 
        -- Standardize laptop naming
        WHEN i.asset_type LIKE '%Laptop%' THEN 
            REPLACE(REPLACE(REPLACE(i.asset_type, '"', ''), ' ', ''), 'Laptop', ' Laptop')
        ELSE i.asset_type 
    END as asset_type,
    i.model,
    i.serial_number,
    i.assigned_to,
    CASE 
        WHEN i.date_assigned = '' THEN NULL 
        ELSE TRY_CAST(i.date_assigned AS DATETIME2)
    END as date_assigned,
    CASE 
        WHEN i.date_decommissioned = '' THEN NULL 
        ELSE TRY_CAST(i.date_decommissioned AS DATETIME2)
    END as date_decommissioned,
    CASE 
        WHEN i.asset_type = 'Loaner Laptop' THEN 1
        WHEN i.notes LIKE '%loaner%' THEN 1
        ELSE 0
    END as is_loaner,
    i.notes,
    'Migration Script'
FROM dbo.Formatted_Company_Inventory i
LEFT JOIN dbo.Locations l ON 
    COALESCE(i.site_name, 'Unknown') = l.site_name AND 
    COALESCE(i.room_number, 'Unknown') = l.room_number
WHERE i.asset_tag IS NOT NULL 
AND i.asset_tag != '';

COMMIT;
GO

-- Step 3: Create Equipment_Loans table
BEGIN TRANSACTION;

CREATE TABLE dbo.Equipment_Loans (
    loan_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    asset_tag VARCHAR(100) NOT NULL REFERENCES dbo.Equipment(asset_tag),
    loaned_to VARCHAR(255) NOT NULL,
    checkout_date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    expected_return_date DATETIME2 NOT NULL,
    actual_return_date DATETIME2 NULL,
    -- Add location tracking for loans
    original_location_id INT REFERENCES dbo.Locations(location_id),
    temporary_location_id INT REFERENCES dbo.Locations(location_id),
    checkout_notes NVARCHAR(MAX) NULL,
    return_notes NVARCHAR(MAX) NULL,
    checked_out_by VARCHAR(255) NOT NULL,
    checked_in_by VARCHAR(255) NULL,
    -- Add audit fields
    created_date DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    created_by VARCHAR(100) NOT NULL,
    last_updated DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    last_updated_by VARCHAR(100) NOT NULL
);

COMMIT;
GO

-- Step 4: Create indexes
BEGIN TRANSACTION;

CREATE INDEX IX_Equipment_AssetType ON dbo.Equipment(asset_type);
CREATE INDEX IX_Equipment_IsLoaner ON dbo.Equipment(is_loaner) INCLUDE (asset_tag, asset_type, model);
CREATE INDEX IX_Equipment_Location ON dbo.Equipment(site_name, room_number);
CREATE INDEX IX_EquipmentLoans_Status ON dbo.Equipment_Loans(actual_return_date) INCLUDE (asset_tag, expected_return_date);
CREATE INDEX IX_EquipmentLoans_Locations ON dbo.Equipment_Loans(original_location_id, temporary_location_id);

COMMIT;
GO

-- Step 5: Create view for active loans
CREATE VIEW dbo.Active_Loans AS
SELECT 
    l.loan_id,
    l.asset_tag,
    e.asset_type,
    e.model,
    e.serial_number,
    -- Include location information
    e.site_name as home_site,
    e.room_number as home_room,
    e.room_name as home_room_name,
    temp_loc.site_name as current_site,
    temp_loc.room_number as current_room,
    temp_loc.room_name as current_room_name,
    -- Loan details
    l.loaned_to,
    l.checkout_date,
    l.expected_return_date,
    l.checkout_notes,
    l.checked_out_by,
    CASE 
        WHEN l.expected_return_date < GETUTCDATE() THEN 1 
        ELSE 0 
    END as is_overdue
FROM dbo.Equipment_Loans l
JOIN dbo.Equipment e ON l.asset_tag = e.asset_tag
LEFT JOIN dbo.Locations temp_loc ON l.temporary_location_id = temp_loc.location_id
WHERE l.actual_return_date IS NULL;
GO
