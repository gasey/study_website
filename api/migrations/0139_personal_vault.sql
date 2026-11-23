BEGIN;

-- Personal Question Vault: learner-owned saved questions, Pro favorites,
-- custom crafted questions with optional images, Leitner mastery boxes, and
-- shareable study packs/tests.

CREATE TABLE IF NOT EXISTS personal_vault_items (
    id text PRIMARY KEY,
    user_id text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind text NOT NULL DEFAULT 'saved' CHECK (kind IN ('saved', 'custom')),
    canonical_question_id text REFERENCES canonical_questions(id) ON DELETE SET NULL,
    folder text NOT NULL DEFAULT 'General',
    subject text NOT NULL DEFAULT 'General',
    question_type text NOT NULL DEFAULT 'mcq' CHECK (question_type IN ('mcq', 'flashcard')),
    question text NOT NULL,
    options jsonb NOT NULL DEFAULT '[]'::jsonb,
    answer_index int,
    answer_text text NOT NULL DEFAULT '',
    explanation text NOT NULL DEFAULT '',
    mnemonic text NOT NULL DEFAULT '',
    image_url text,
    image_alt text NOT NULL DEFAULT '',
    difficulty text NOT NULL DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard', 'trap')),
    tags jsonb NOT NULL DEFAULT '[]'::jsonb,
    is_favorite boolean NOT NULL DEFAULT false,
    mastery_box int NOT NULL DEFAULT 1 CHECK (mastery_box BETWEEN 1 AND 4),
    review_count int NOT NULL DEFAULT 0,
    correct_count int NOT NULL DEFAULT 0,
    last_reviewed_at timestamptz,
    next_review_at timestamptz,
    source_meta jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_personal_vault_user_canonical
    ON personal_vault_items (user_id, canonical_question_id)
    WHERE canonical_question_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_personal_vault_user_updated
    ON personal_vault_items (user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_personal_vault_user_due
    ON personal_vault_items (user_id, next_review_at)
    WHERE next_review_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS personal_vault_shares (
    token text PRIMARY KEY,
    owner_id text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title text NOT NULL,
    description text NOT NULL DEFAULT '',
    mode text NOT NULL DEFAULT 'practice' CHECK (mode IN ('practice', 'timed', 'flashcards')),
    duration_minutes int NOT NULL DEFAULT 10 CHECK (duration_minutes BETWEEN 1 AND 180),
    items jsonb NOT NULL DEFAULT '[]'::jsonb,
    clones_count int NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_personal_vault_shares_owner
    ON personal_vault_shares (owner_id, created_at DESC);

GRANT SELECT, INSERT, UPDATE, DELETE ON personal_vault_items, personal_vault_shares TO mpsc;

COMMIT;
