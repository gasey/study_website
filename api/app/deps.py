import re
from typing import Annotated

from fastapi import Header, HTTPException

from .db import cursor

# A device id is a client-generated UUID kept in localStorage. It is not
# authentication — it identifies a browser, not a person, and anyone can
# forge one. That is acceptable for recording practice progress and nothing
# else: never gate anything that matters on it. Real accounts land later and
# adopt the device's history.
_DEVICE_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

DeviceId = Annotated[str | None, Header(alias="X-Device-Id")]


async def current_user(x_device_id: DeviceId = None) -> str:
    """Resolve the device header to a users row, creating it on first sight.

    Returns the users.id. Raises 400 if the header is missing or malformed —
    the client always has one, so a missing header means a bug, not a guest.
    """
    if not x_device_id or not _DEVICE_RE.match(x_device_id):
        raise HTTPException(400, "missing or malformed X-Device-Id")

    uid = f"dev_{x_device_id}"
    async with cursor() as cur:
        # handle is UNIQUE; the short suffix keeps anonymous handles readable
        # in the admin without being guessable from the id alone.
        await cur.execute(
            """INSERT INTO users (id, handle, role)
               VALUES (%s, %s, 'learner')
               ON CONFLICT (id) DO NOTHING""",
            (uid, f"anon-{x_device_id[:8]}"),
        )
    return uid
