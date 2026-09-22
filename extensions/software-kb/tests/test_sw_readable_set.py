"""The `sw_*` read surfaces return only rows from KBs the caller may read (#223).

Each of these tools declares `kb_name` optionally, so a call that omits it is
refused for a scoped caller by the MCP chokepoint rather than served the index.
They pass the caller's readable set into the query through `kb_scope_clause`,
the rule the other extensions use, so the four branches are the same
everywhere: a named KB binds, a set narrows, an empty set matches nothing, and
`None` stays unscoped.

These drive a real `PyriteDB` rather than a stub, because the narrowing is the
storage query's job (`kb_name` and the clause compose) and a stub would only
test the stub.
"""

import json
from pathlib import Path

import pytest
from pyrite_software_kb.plugin import SoftwareKBPlugin

from pyrite.storage.database import PyriteDB

PUBLIC, PRIVATE = "public-kb", "private-kb"

# Every handler that was in OPTIONAL_KB_TOOLS for this extension, with the entry
# type it reads. `_mcp_create_adr` is absent on purpose: it writes an ADR, so a
# behavioural test would create one; its read (finding the next ADR number) is
# narrowed by the same helper as `_mcp_adrs`, which is covered here.
SW_SURFACES = [
    ("_mcp_adrs", "adr"),
    ("_mcp_component", "component"),
    ("_mcp_standards", "standard"),
    ("_mcp_validations", "programmatic_validation"),
    ("_mcp_conventions", "development_convention"),
    ("_mcp_backlog", "backlog_item"),
    ("_mcp_epics", "backlog_item"),
    ("_mcp_milestones", "milestone"),
    ("_mcp_review_queue", "backlog_item"),
    ("_mcp_board", "backlog_item"),
    ("_mcp_pull_next", "backlog_item"),
]

# Surfaces that echo every matching row, used to show the filter is what
# removed the private row rather than the handler returning nothing for an
# unrelated reason.
NON_VACUITY_SURFACES = [
    ("_mcp_adrs", "adr"),
    ("_mcp_component", "component"),
    ("_mcp_standards", "standard"),
    ("_mcp_backlog", "backlog_item"),
    ("_mcp_milestones", "milestone"),
]


def _make_db(tmp_path, entry_type):
    db = PyriteDB(Path(tmp_path) / "index.db")
    for kb in (PUBLIC, PRIVATE):
        db._raw_conn.execute(
            "INSERT OR IGNORE INTO kb (name, path, kb_type) VALUES (?, ?, ?)",
            (kb, str(tmp_path), "software"),
        )
        db._raw_conn.execute(
            "INSERT OR IGNORE INTO entry (id, kb_name, entry_type, title, body, metadata,"
            "importance, status, priority, created_at, updated_at) VALUES (?, ?, ?, ?, '', ?,"
            " 5, 'accepted', 'medium', '2026-01-01T00:00:00', '2026-01-02T00:00:00')",
            (
                f"{kb}-{entry_type}",
                kb,
                entry_type,
                f"{kb} {entry_type}",
                json.dumps(
                    {
                        "adr_number": 1,
                        "kind": "epic",
                        "category": "coding",
                        "review_status": "under_review",
                    }
                ),
            ),
        )
    db._raw_conn.commit()
    return db


def _plugin_for(db):
    plugin = SoftwareKBPlugin()
    plugin._get_db = lambda: (db, False)
    return plugin


def _call(tmp_path, handler, entry_type, **kwargs):
    db = _make_db(tmp_path, entry_type)
    try:
        return json.dumps(getattr(_plugin_for(db), handler)({}, **kwargs))
    finally:
        db.close()


@pytest.mark.parametrize("handler,entry_type", NON_VACUITY_SURFACES)
class TestThePrivateRowIsReachableWhenUnscoped:
    def test_unscoped_call_does_reach_the_private_kb(self, tmp_path, handler, entry_type):
        out = _call(tmp_path, handler, entry_type)
        assert f"{PUBLIC}-{entry_type}" in out
        assert f"{PRIVATE}-{entry_type}" in out

    def test_the_readable_set_is_what_removes_it(self, tmp_path, handler, entry_type):
        out = _call(tmp_path, handler, entry_type, readable_kbs={PUBLIC})
        assert f"{PUBLIC}-{entry_type}" in out
        assert f"{PRIVATE}-{entry_type}" not in out


@pytest.mark.parametrize("handler,entry_type", SW_SURFACES)
def test_no_read_surface_serves_an_unreadable_kb(tmp_path, handler, entry_type):
    scoped = _call(tmp_path, handler, entry_type, readable_kbs={PUBLIC})
    assert f"{PRIVATE}-{entry_type}" not in scoped

    empty = _call(tmp_path, handler, entry_type, readable_kbs=set())
    assert f"{PUBLIC}-{entry_type}" not in empty
    assert f"{PRIVATE}-{entry_type}" not in empty
