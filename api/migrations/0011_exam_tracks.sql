-- Curated exam tracks. The paper IDs are resolved once from explicit titles
-- and saved into the section filters; request-time code never guesses by name.
BEGIN;

INSERT INTO collections (id,title,kind,route,visibility,position,live_version) VALUES
 ('ldc','Lower Division Clerk (LDC)','exam','/exams/ldc','public',10,1),
 ('udc','Upper Division Clerk (UDC)','exam','/exams/udc','public',11,1),
 ('assistant','Assistant Grade','exam','/exams/assistant','public',12,1),
 ('combined-prelims','Mizoram Civil Services Prelims','exam','/exams/combined-prelims','public',13,1),
 ('group-b-gazetted','Group B · Gazetted','exam','/exams/group-b-gazetted','public',14,1),
 ('group-b-non-gazetted','Group B · Non-Gazetted','exam','/exams/group-b-non-gazetted','public',15,1)
ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title,visibility='public',live_version=1;

INSERT INTO collection_sections (collection_id,version,path,title,position,formats,query,note)
SELECT c.id,1,'papers','Past papers',0,'{}',jsonb_build_object('paper_ids',p.ids),c.note
FROM (VALUES
 ('ldc','Lower Division Clerk · direct recruitment',NULL::text),
 ('udc','Upper Division Clerk · direct recruitment',NULL),
 ('assistant','Assistant Grade · direct recruitment',NULL),
 ('combined-prelims','MCS combined preliminary examinations',NULL),
 ('group-b-gazetted','Group B Gazetted · mapped papers only','Current mapped coverage is limited to historical departmental Inspector (Group B Gazetted) papers. Combined gazetted recruitment papers are not yet in this bank.'),
 ('group-b-non-gazetted','Group B Non-Gazetted · direct recruitment',NULL)
) AS c(id,title,note)
CROSS JOIN LATERAL (
 SELECT COALESCE(array_agg(p.id ORDER BY p.year,p.id),ARRAY[]::text[]) AS ids
 FROM papers p
 WHERE CASE c.id
   WHEN 'ldc' THEN p.exam_type IN ('Direct','Direct_NG') AND lower(p.exam_name) LIKE '%lower division clerk%' AND lower(p.exam_name) NOT LIKE '%limited departmental%'
   WHEN 'udc' THEN p.exam_type IN ('Direct','Direct_NG') AND (lower(p.exam_name) LIKE '%upper division clerk%' OR lower(p.exam_name) LIKE '%assistant grade & udc%') AND lower(p.exam_name) NOT LIKE '%limited departmental%'
   WHEN 'assistant' THEN p.exam_type IN ('Direct','Direct_NG') AND (lower(p.exam_name) LIKE '%assistant grade under government of mizoram%' OR lower(p.exam_name) LIKE '%assistant grade under mpsc%' OR lower(p.exam_name) LIKE '%assistant grade & udc%') AND lower(p.exam_name) NOT LIKE '%limited departmental%'
   WHEN 'combined-prelims' THEN p.exam_type='Direct' AND lower(p.exam_name) LIKE '%mcs combined%prelim%'
   WHEN 'group-b-gazetted' THEN p.exam_type='Departmental' AND lower(p.exam_name) LIKE '%inspector%group%gazetted%'
   WHEN 'group-b-non-gazetted' THEN p.exam_type='Direct_NG' AND lower(p.exam_name) ~ 'group.?[''’]?b.*non.?gazetted'
   ELSE false END
) p
ON CONFLICT (collection_id,version,path) DO UPDATE SET title=EXCLUDED.title,query=EXCLUDED.query,note=EXCLUDED.note;

COMMIT;
