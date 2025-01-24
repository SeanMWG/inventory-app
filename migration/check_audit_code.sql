-- Let's look at some sample audit records to understand the tracking
SELECT TOP 100
    asset_tag,
    action_type,
    field_name,
    old_value,
    new_value,
    changed_by,
    changed_at,
    notes
FROM dbo.inventory_audit_log
ORDER BY changed_at DESC;
