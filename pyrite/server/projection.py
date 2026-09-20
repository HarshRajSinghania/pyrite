"""Field projection shared by the REST read routes.

`?fields=` is advertised on `GET /api/entries/{id}` and `GET /api/search`. The
response models (`EntryResponse`, `SearchResult`) require `id`, `kb_name`,
`entry_type` and `title`, so a projection that drops any of them made a valid
`?fields=title` request fail validation — a 500 on the entry route and a 400
with a raw validation dump on search (issue #179).

Keeping those fields in every projection is the same identity guarantee the MCP
tools give; the endpoints return the projected payload directly so requested
fields outside the response model survive too.
"""

from __future__ import annotations

from typing import Any

# Fields the REST response models require, so a projection can never drop them.
REQUIRED_RESPONSE_FIELDS: tuple[str, ...] = ("id", "kb_name", "entry_type", "title")


def parse_fields_param(fields: str | None) -> list[str] | None:
    """Split a comma-separated ``?fields=`` value into a clean field list."""
    if not fields:
        return None
    parsed = [f.strip() for f in fields.split(",") if f.strip()]
    return parsed or None


def project_fields(entry: dict[str, Any], fields: list[str] | None) -> dict[str, Any]:
    """Reduce ``entry`` to ``fields`` plus the fields the response models require."""
    if not fields:
        return entry
    keys = dict.fromkeys((*REQUIRED_RESPONSE_FIELDS, *fields))
    return {k: entry[k] for k in keys if k in entry}
