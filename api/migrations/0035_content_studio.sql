BEGIN;
ALTER TABLE materials ADD COLUMN revision INTEGER NOT NULL DEFAULT 1,ADD COLUMN lock_version INTEGER NOT NULL DEFAULT 1,ADD COLUMN published_revision INTEGER,ADD COLUMN workflow_state TEXT NOT NULL DEFAULT 'draft' CHECK(workflow_state IN ('draft','submitted','changes_requested','published','archived'));
CREATE TABLE material_revisions(material_id TEXT NOT NULL REFERENCES materials(id),revision INTEGER NOT NULL,payload JSONB NOT NULL,created_by TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(material_id,revision));
CREATE TRIGGER immutable_material_revision BEFORE UPDATE OR DELETE ON material_revisions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE material_events(id BIGSERIAL PRIMARY KEY,material_id TEXT NOT NULL REFERENCES materials(id),actor_id TEXT NOT NULL,action TEXT NOT NULL,detail JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TRIGGER immutable_material_event BEFORE UPDATE OR DELETE ON material_events FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE material_bookmarks(material_id TEXT NOT NULL REFERENCES materials(id),user_id TEXT NOT NULL REFERENCES users(id),created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(material_id,user_id));
CREATE TABLE material_reports(id BIGSERIAL PRIMARY KEY,material_id TEXT NOT NULL REFERENCES materials(id),user_id TEXT NOT NULL REFERENCES users(id),reason TEXT NOT NULL,note TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'open' CHECK(state IN ('open','resolved')),resolution TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),UNIQUE(material_id,user_id));
CREATE INDEX materials_workflow ON materials(workflow_state,updated_at DESC);
CREATE INDEX material_reports_open ON material_reports(created_at DESC) WHERE state='open';
-- Preserve any pre-CMS material as a revision; no raw HTML is introduced.
INSERT INTO material_revisions(material_id,revision,payload,created_by)
 SELECT id,1,jsonb_build_object('title',title,'summary','','preview','','kind','note','access','free','price_paise',0,'tags',tags,'blocks',blocks,'collection_id',NULL,'subject_id',NULL),author_id FROM materials;
UPDATE materials SET published_revision=1,workflow_state='published' WHERE status='published';
UPDATE materials SET workflow_state='archived' WHERE status='removed';
-- Explicitly requested public demo: presentation copy, not a purchased product.
INSERT INTO materials(id,author_id,title,tags,blocks,status,published_at,published_revision,workflow_state)
VALUES('cms-paid-demo','team','Paid content preview · demo',ARRAY['Platform demo'],'[]','published',now(),1,'published');
INSERT INTO material_revisions(material_id,revision,created_by,payload) VALUES('cms-paid-demo',1,'system:demo',
'{"title":"Paid content preview · demo","summary":"Explore a sample preview and locked lesson. No purchase or payment is available in this demo.","preview":"A useful study guide begins with a clear learning goal, a short lesson and a chance to practise. This excerpt demonstrates what a reader can inspect before choosing paid content.","kind":"lesson","access":"paid-preview","price_paise":4900,"tags":["Platform demo"],"collection_id":null,"subject_id":null,"blocks":[{"id":"demo-heading","type":"heading","text":"Inside the full lesson"},{"id":"demo-body","type":"paragraph","text":"This is demonstration-only premium content. The published reader does not receive this protected body without author or owner access. Later, verified purchases can grant content-specific access without changing learning XP or bank answers."},{"id":"demo-tip","type":"callout","text":"Future creator sales need purchase verification, buyer access, refund handling and creator settlement before launch."}]}'::jsonb);
INSERT INTO material_events(material_id,actor_id,action,detail) VALUES('cms-paid-demo','system:demo','demo_published','{"demo":true,"payments_enabled":false}');
GRANT SELECT,INSERT,UPDATE ON materials,material_votes,material_bookmarks,material_reports TO mpsc;
GRANT DELETE ON material_bookmarks TO mpsc;
GRANT SELECT,INSERT ON material_revisions,material_events TO mpsc;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;
ALTER TABLE review_notifications ADD COLUMN material_id TEXT REFERENCES materials(id);
ALTER TABLE reward_ledger DROP CONSTRAINT reward_ledger_kind_check;
ALTER TABLE reward_ledger ADD CONSTRAINT reward_ledger_kind_check CHECK(kind IN ('study','game','contribution','content','redemption','adjustment'));
CREATE TABLE material_reward_claims(material_id TEXT PRIMARY KEY REFERENCES materials(id),user_id TEXT NOT NULL REFERENCES users(id),xp INTEGER NOT NULL,points INTEGER NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),reversed_at TIMESTAMPTZ);
GRANT SELECT,INSERT,UPDATE ON material_reward_claims TO mpsc;
COMMIT;
