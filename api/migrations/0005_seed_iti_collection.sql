-- Seed the first exam collection: ITI Instructor 2026.
--
-- An exam here is a saved filter set over the bank, not a copy of questions
-- (collections / collection_sections / collection_papers). Those tables were
-- empty, so nothing in Phase 2 could be built against real data.
--
-- Chosen on the data: 16 papers, 1,446 questions with an OFFICIAL key — the
-- best-keyed exam in the bank. UDC/LDC would have been the natural first
-- choice but has no keyed papers at all.
--
-- Sections filter by paper_id, because `subject` is NULL on every row until
-- classification runs. They can gain subject filters later without changing
-- this seed. Trades are matched by keyword rather than by parsing filenames:
-- the names are inconsistent enough ("Paper-IV (Technical Paper-IV)
-- (Wireman)") that parsing split single trades across two sections.

BEGIN;

INSERT INTO collections (id, title, kind, route, visibility, position, live_version)
VALUES ('iti-instructor-2026', 'ITI Instructor 2026', 'exam',
        '/exams/iti-instructor-2026', 'public', 0, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO collection_sections (collection_id, version, path, title, position, formats, query) VALUES
  ('iti-instructor-2026', 1, 'general/english', 'Paper-I · General English', 0, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'general/knowledge', 'Paper-II · General Knowledge', 1, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-II (General Knowledge)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/copa', 'COPA', 2, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III (COPA-Technical Paper-I)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (COPA-Technical Paper-II..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/electrician', 'Electrician', 3, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III (Electrician - Technical Paper-I)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (Electrician - Technical Paper-II)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/electronics-mechanic', 'Electronics Mechanic', 4, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I -Electronics Mechanics)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II -Electronics Mechanics)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/wireman', 'Wireman', 5, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I) (Wireman)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-IV) (Wireman)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/baker-confectioner', 'Baker & Confectioner', 6, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I-Baker & Confectioner)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II-Baker & Confectioner)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/carpenter', 'Carpenter', 7, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Paper-III-Technical Paper-I (Carpenter)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV- Technical Paper-II (Carpenter)..pdf"]}'::jsonb),
  ('iti-instructor-2026', 1, 'technical/workshop-calculation-science', 'Workshop Calculation & Science', 8, '{}', '{"paper_ids": ["Old_Questions/Direct_2025-2027/Technical Paper-III (Workshop Calculation & Science-Technical Paper-I)..pdf", "Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II -Workshop Calculation & Science)..pdf"]}'::jsonb)
ON CONFLICT (collection_id, version, path) DO NOTHING;

INSERT INTO collection_papers (collection_id, version, paper_id, as_mock) VALUES
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-II (General Knowledge)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III (COPA-Technical Paper-I)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III (Electrician - Technical Paper-I)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I -Electronics Mechanics)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I) (Wireman)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III (Technical Paper-I-Baker & Confectioner)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-III-Technical Paper-I (Carpenter)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Technical Paper-III (Workshop Calculation & Science-Technical Paper-I)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (COPA-Technical Paper-II..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (Electrician - Technical Paper-II)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II -Electronics Mechanics)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II -Workshop Calculation & Science)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-II-Baker & Confectioner)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV (Technical Paper-IV) (Wireman)..pdf', true),
  ('iti-instructor-2026', 1, 'Old_Questions/Direct_2025-2027/Paper-IV- Technical Paper-II (Carpenter)..pdf', true)
ON CONFLICT (collection_id, version, paper_id) DO NOTHING;

COMMIT;
