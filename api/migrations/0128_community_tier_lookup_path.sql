BEGIN;
-- PostgreSQL searches the implicit temporary relation schema before a configured
-- search_path unless pg_temp is named explicitly. App-created temporary vote or
-- attempt relations must never influence server-owned milestone capture. Keep
-- public before pg_temp for all tier readers/writers and the audit guard; preserve
-- function bodies, owners, grants, source records and immutable history.
ALTER FUNCTION community_weighted_helpful(text) SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION community_record_tier(text) SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION community_tier_change() SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION community_display_tier_rank(text) SET search_path=pg_catalog,public,pg_temp;
ALTER FUNCTION community_tier_event_guard() SET search_path=pg_catalog,public,pg_temp;
COMMIT;
