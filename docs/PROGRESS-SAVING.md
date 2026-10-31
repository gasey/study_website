# Progress saving

## One answer history, several views

Completed answers are written to `attempts` against the canonical question ID. Each row also records the learner, time, result, selected option text, and where the practice happened (`collection_id`, `paper_id`, `section_path`, and context). A question can therefore be reused by several exam modules without duplicating either the question or the learner's history.

The profile shows the overall rollup. Exam pages show module rollups, and module progress can break those down by section. These are filtered summaries of the same history, not separate progress stores. Accuracy is based on answer events; unique questions are counted separately so retries remain visible without inflating coverage.

## Timed papers

An open mock is a resumable draft. `mock_session_answers` stores the current choice and review flag for each frozen question, while `mock_sessions.current_position` stores the learner's place in the paper. Reloading the page restores answers, review marks, and position. On submission, choices are scored and copied into the completed answer history.

## Identity and syncing

Anonymous browser progress is identified by a UUID stored in local storage. A signed-in request resolves to the account ID. Bank attempts remain attached to the identity used when each answer was submitted; automatic merging of pre-login attempt history is not implemented. Guided lesson cache entries missing from the active identity's backend record are uploaded when the module loads.

## Scope

- Overall account/browser progress: omit `collection_id`.
- One exam module: filter by `collection_id`.
- One module section: filter by both `collection_id` and `section_path`.
- A paper: each attempt retains `paper_id`, which supports a later paper-level rollup without changing the stored history.

No learner history is deleted or rewritten when a question moves between modules or its classification changes.

## Guided lessons

Short lesson visits and concept-check results use `module_learning_progress`, keyed by the resolved browser device or signed-in account, module, and stable lesson ID. The browser keeps a local cache for immediate display and offline fallback, then syncs it to `/api/me/learning-progress/{module_id}`. Concept checks are teaching examples and do not enter canonical question scoring or attempt history. Existing bank questions continue to use `attempts` and the shared answer endpoint.
