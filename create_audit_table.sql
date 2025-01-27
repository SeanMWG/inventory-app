-- Create audit log table
CREATE TABLE dbo.Inventory_Audit_Log (
    audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    action_type VARCHAR(10) NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    asset_tag VARCHAR(100) NOT NULL,   -- Reference to the asset being modified
    field_name VARCHAR(100) NOT NULL,  -- Name of the field that changed
    old_value NVARCHAR(MAX) NULL,      -- Previous value (NULL for INSERT)
    new_value NVARCHAR(MAX) NULL,      -- New value (NULL for DELETE)
    changed_by VARCHAR(255) NOT NULL,  -- User who made the change
    changed_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    notes NVARCHAR(MAX) NULL           -- Any additional context
);
