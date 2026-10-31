BEGIN;
-- Bank-owned secondary paths; proposals publish through the same local bank workflow.
CREATE TABLE question_topic_links (
 question_id TEXT NOT NULL REFERENCES canonical_questions(id) ON DELETE CASCADE,
 path_id TEXT NOT NULL,
 subject_id TEXT NOT NULL, subject_label TEXT NOT NULL,
 topic_id TEXT, topic_label TEXT, subtopic_id TEXT, subtopic_label TEXT,
 taxonomy_version TEXT NOT NULL, source TEXT NOT NULL,
 review_status TEXT NOT NULL CHECK(review_status IN ('approved','pending','rejected')),
 evidence TEXT NOT NULL,
 CHECK(path_id=COALESCE(subtopic_id,topic_id,subject_id)),
 CHECK(subtopic_id IS NULL OR topic_id IS NOT NULL),
 PRIMARY KEY(question_id,path_id)
);
CREATE INDEX question_topic_links_subject ON question_topic_links(subject_id,review_status);
CREATE INDEX question_topic_links_topic ON question_topic_links(topic_id,review_status);
CREATE VIEW v_question_paths AS
 SELECT question_id,subject_id,subject_label,topic_id,topic_label,subtopic_id,subtopic_label,true AS is_primary,'approved'::text AS review_status
 FROM question_classifications WHERE review_status='approved'
 UNION
 SELECT question_id,subject_id,subject_label,topic_id,topic_label,subtopic_id,subtopic_label,false,'approved'::text
 FROM question_topic_links WHERE review_status='approved';
CREATE TABLE library_shelves (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
 match_ids TEXT[] NOT NULL CHECK(cardinality(match_ids)>0), position INTEGER NOT NULL,
 active BOOLEAN NOT NULL DEFAULT true
);
INSERT INTO library_shelves(id,title,description,match_ids,position) VALUES
 ('geography','Geography','India, the world, places and physical geography.',ARRAY['geography','general-studies/geography'],1),
 ('history','History','Indian and world history in one place.',ARRAY['history','general-studies/indian-history','general-studies/world-history'],2),
 ('polity','Polity','Constitution, institutions and government.',ARRAY['polity','general-studies/indian-polity'],3),
 ('economy','Economy','Indian economy and economic ideas.',ARRAY['economics','general-studies/indian-economy'],4),
 ('science','Science','Physics, chemistry and biology.',ARRAY['science'],5),
 ('environment','Environment','Ecology, biodiversity and conservation.',ARRAY['environment','general-studies/environment'],6),
 ('mizoram-gk','Mizoram GK','Mizoram history, places and public life.',ARRAY['general-studies/mizoram'],7),
 ('current-affairs','Current Affairs','Events as asked in their original year.',ARRAY['general-studies/current-affairs'],8);
GRANT SELECT ON v_question_paths,library_shelves TO mpsc;
GRANT SELECT,INSERT,UPDATE,DELETE ON question_topic_links TO mpsc;
COMMIT;
