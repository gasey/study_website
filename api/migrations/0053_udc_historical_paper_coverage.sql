-- Exact source-file identities reviewed for the UDC direct recruitment track.
-- Publish a new collection version; retain the previous version for recovery.
-- This changes discovery membership, never source answers or scoring provenance.
BEGIN;
CREATE TEMP TABLE udc_paper_additions(id TEXT PRIMARY KEY) ON COMMIT DROP;
INSERT INTO udc_paper_additions(id) VALUES
 ('Old_Questions/Direct_2014-2018/1.UDC (Contract) 2016-Cooperation Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC (contract) 2016 Art& Culture Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC Direct-2014 Health Deptt.& Co-operation Dept..Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC Excise Deptt. Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC under Agriculture Deptt. Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC under EF&CC Deptt. Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC under SAD Paper-I.pdf'),
 ('Old_Questions/Direct_2014-2018/1.UDC under Tourism Deptt.-I.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC (Contract) 2016-Cooperation Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC (contract) 2016 Art& Culture Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC Direct-2014 Health Deptt.& Co-operation Dept.Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC Excise Deptt. Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC under Agriculture Deptt. Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC under EF&CC Deptt. Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC under SAD Paper-II.pdf'),
 ('Old_Questions/Direct_2014-2018/2.UDC under Tourism Deptt.-II.pdf');
DO $$
DECLARE current_version INTEGER; draft INTEGER;
BEGIN
 SELECT live_version,draft_version INTO current_version,draft FROM collections WHERE id='udc' FOR UPDATE;
 IF current_version IS DISTINCT FROM 1 OR draft IS NOT NULL
 THEN RAISE EXCEPTION 'UDC collection changed; review the manifest against its current version'; END IF;
 IF EXISTS(SELECT 1 FROM collection_sections WHERE collection_id='udc' AND version=2)
 OR EXISTS(SELECT 1 FROM collection_papers WHERE collection_id='udc' AND version=2)
 THEN RAISE EXCEPTION 'UDC version 2 already exists; do not overwrite it'; END IF;
 IF (SELECT count(*) FROM collection_papers WHERE collection_id='udc' AND version=1)<>28
 THEN RAISE EXCEPTION 'UDC prior paper manifest changed'; END IF;
 IF (SELECT count(*) FROM papers p JOIN udc_paper_additions n ON n.id=p.id
     WHERE p.exam_type IN ('Direct','Direct_NG') AND p.exam_scope_id='mizoram-recruitment')<>18
 THEN RAISE EXCEPTION 'A reviewed direct recruitment paper is missing or outside the Mizoram scope'; END IF;
END $$;
INSERT INTO collection_sections(collection_id,version,path,title,position,formats,query,pins,excludes,note)
 SELECT collection_id,2,path,title,position,formats,
 CASE WHEN path='papers' THEN jsonb_set(query,'{paper_ids}',
    (SELECT jsonb_agg(id ORDER BY id) FROM (
       SELECT jsonb_array_elements_text(query->'paper_ids') AS id
       UNION SELECT id FROM udc_paper_additions) ids)) ELSE query END,
 pins,excludes,note FROM collection_sections WHERE collection_id='udc' AND version=1;
INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path,display_title,
 duration_minutes,marks_correct,marks_wrong,instructions,allow_browse,allow_practice,rule_source)
 SELECT collection_id,2,paper_id,as_mock,section_path,display_title,duration_minutes,
 marks_correct,marks_wrong,instructions,allow_browse,allow_practice,rule_source
 FROM collection_papers WHERE collection_id='udc' AND version=1;
INSERT INTO collection_papers(collection_id,version,paper_id,as_mock,section_path,display_title,
 duration_minutes,marks_correct,marks_wrong,allow_browse,allow_practice,rule_source)
 SELECT 'udc',2,p.id,false,'papers',p.exam_name||COALESCE(' · '||p.year::text,''),
 NULL,1,0,true,true,'platform-default' FROM papers p JOIN udc_paper_additions n ON n.id=p.id;
DO $$ BEGIN
 IF (SELECT count(*) FROM collection_papers WHERE collection_id='udc' AND version=2)<>46
 OR (SELECT jsonb_array_length(query->'paper_ids') FROM collection_sections WHERE collection_id='udc' AND version=2 AND path='papers')<>46
 THEN RAISE EXCEPTION 'UDC version 2 manifest is incomplete'; END IF;
END $$;
UPDATE collections SET live_version=2,updated_at=now() WHERE id='udc';
COMMIT;
