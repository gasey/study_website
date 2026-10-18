from fastapi import APIRouter, HTTPException

from ..db import cursor
from ..schemas import CollectionDetail, CollectionSection, CollectionSummary

router = APIRouter(prefix="/api/collections", tags=["collections"])

# An exam is a saved filter set over the bank, not a copy of questions.
# Sections currently filter on query->'paper_ids'; when classification runs
# they will also be able to filter on subject, without changing this shape.
# Counts come from v_scorable, so a section can never advertise questions
# that mocks are not allowed to score. See CLAUDE.md rule 1.
_SECTION_COUNT = """
    SELECT COUNT(*) FROM v_scorable v
      JOIN appearances a ON a.canonical_id = v.id
     WHERE a.paper_id IN (SELECT jsonb_array_elements_text(s.query -> 'paper_ids'))
"""


@router.get("", response_model=list[CollectionSummary])
async def list_collections() -> list[CollectionSummary]:
    async with cursor() as cur:
        await cur.execute(
            f"""SELECT c.id, c.title, c.kind, c.route, c.visibility,
                       COUNT(s.*)::int AS sections,
                       COALESCE(SUM(({_SECTION_COUNT}))::int, 0) AS scorable
                  FROM collections c
                  LEFT JOIN collection_sections s
                         ON s.collection_id = c.id AND s.version = c.live_version
                 WHERE c.visibility = 'public'
                 GROUP BY c.id, c.title, c.kind, c.route, c.visibility, c.position
                 ORDER BY c.position, c.title"""
        )
        return [CollectionSummary(**r) for r in await cur.fetchall()]


@router.get("/{collection_id}", response_model=CollectionDetail)
async def get_collection(collection_id: str) -> CollectionDetail:
    async with cursor() as cur:
        await cur.execute(
            "SELECT id, title, kind, route, visibility, live_version FROM collections WHERE id = %s",
            (collection_id,),
        )
        head = await cur.fetchone()
        if head is None or head["visibility"] != "public":
            raise HTTPException(404, "collection not found")

        await cur.execute(
            f"""SELECT s.path, s.title, s.position, s.formats,
                       jsonb_array_length(s.query -> 'paper_ids') AS papers,
                       ({_SECTION_COUNT})::int AS scorable
                  FROM collection_sections s
                 WHERE s.collection_id = %s AND s.version = %s
                 ORDER BY s.position""",
            (collection_id, head["live_version"]),
        )
        sections = [CollectionSection(**r) for r in await cur.fetchall()]

    return CollectionDetail(
        id=head["id"], title=head["title"], kind=head["kind"], route=head["route"],
        visibility=head["visibility"],
        sections=len(sections),
        scorable=sum(s.scorable for s in sections),
        section_list=sections,
    )
