BEGIN;
CREATE TABLE exam_scopes (
 id TEXT PRIMARY KEY,title TEXT NOT NULL,launch_enabled BOOLEAN NOT NULL DEFAULT false
);
INSERT INTO exam_scopes VALUES ('mizoram-recruitment','MPSC & Mizoram recruitment exams',true),('outside-mizoram','Other exam systems',false);
ALTER TABLE papers ADD COLUMN exam_scope_id TEXT REFERENCES exam_scopes(id);
ALTER TABLE collections ADD COLUMN exam_scope_id TEXT REFERENCES exam_scopes(id);
-- User-confirmed launch corpus, audited: all 1,938 existing source papers are
-- from this MPSC/Mizoram archive. No default is assigned to future imports.
UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE source_file LIKE 'Old_Questions/%' OR id LIKE 'Old_Questions/%';
UPDATE collections SET exam_scope_id='mizoram-recruitment';
CREATE INDEX papers_exam_scope ON papers(exam_scope_id,id);
CREATE INDEX collections_exam_scope ON collections(exam_scope_id,visibility);
CREATE VIEW launch_question_ids AS SELECT DISTINCT a.canonical_id FROM appearances a JOIN papers p ON p.id=a.paper_id WHERE p.exam_scope_id='mizoram-recruitment';
CREATE VIEW v_launch_all AS SELECT v.* FROM v_all_questions v WHERE v.id IN (SELECT canonical_id FROM launch_question_ids);
CREATE VIEW v_launch_practice AS SELECT v.* FROM v_practice v WHERE v.id IN (SELECT canonical_id FROM launch_question_ids);
CREATE VIEW v_launch_scorable AS SELECT v.* FROM v_scorable v WHERE v.id IN (SELECT canonical_id FROM launch_question_ids);
CREATE VIEW v_launch_mock_practice AS SELECT v.* FROM v_mock_practice v WHERE v.id IN (SELECT canonical_id FROM launch_question_ids);
GRANT SELECT ON exam_scopes,launch_question_ids,v_launch_all,v_launch_practice,v_launch_scorable,v_launch_mock_practice TO mpsc;
COMMIT;
