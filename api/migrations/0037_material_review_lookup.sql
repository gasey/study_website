BEGIN;
-- Latest feedback and review history stay bounded by the selected material.
CREATE INDEX material_events_material_history ON material_events(material_id,id DESC);
COMMIT;
