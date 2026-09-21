"""The cascade list tools narrow to the caller's readable KBs (#223).

Each of the five declares `kb_name` optionally, and four of them *default* it to
a specific KB. That default is the interesting case: a scoped caller who omits
the name is refused by the MCP chokepoint rather than served a KB they may not
read, and the handlers pass the readable set to `list_entries` alongside the
name, so the default is served only when it is readable.

These drive a real `PyriteDB` rather than a stub, because the narrowing is the
storage query's job (`kb_name` and `kb_names` compose), and a stub would only
test the stub.
"""

import json
from pathlib import Path

import pytest
from pyrite_cascade.plugin import CascadePlugin

from pyrite.storage.database import PyriteDB

KBS = ("cascade-research", "cascade-timeline", "cascade-solidarity", "private-kb")


def _make_db(tmp_path, entries):
    db = PyriteDB(Path(tmp_path) / "index.db")
    for kb in KBS:
        db._raw_conn.execute(
            "INSERT INTO kb (name, path, kb_type) VALUES (?, ?, ?)",
            (kb, str(tmp_path), "generic"),
        )
    for entry in entries:
        db._raw_conn.execute(
            "INSERT INTO entry (id, kb_name, entry_type, title, body, metadata, importance,"
            " created_at, updated_at) VALUES (?, ?, ?, ?, '', ?, ?, '2026-01-01T00:00:00',"
            " '2026-01-01T00:00:00')",
            (
                entry["id"],
                entry["kb_name"],
                entry["entry_type"],
                entry.get("title", entry["id"]),
                json.dumps(entry.get("meta", {})),
                entry.get("importance", 5),
            ),
        )
    db._raw_conn.commit()
    return db


def _plugin_for(db):
    plugin = CascadePlugin()
    plugin._get_db = lambda: (db, False)
    return plugin


@pytest.fixture
def db(tmp_path):
    return _make_db(
        tmp_path,
        [
            {
                "id": "pub-actor",
                "kb_name": "cascade-research",
                "entry_type": "actor",
                "meta": {"capture_lanes": ["lane-a"]},
            },
            {
                "id": "priv-actor",
                "kb_name": "private-kb",
                "entry_type": "actor",
                "meta": {"capture_lanes": ["lane-a"]},
            },
            {
                "id": "pub-event",
                "kb_name": "cascade-timeline",
                "entry_type": "timeline_event",
                "meta": {},
            },
            {
                "id": "priv-event",
                "kb_name": "private-kb",
                "entry_type": "timeline_event",
                "meta": {},
            },
            {
                "id": "pub-solidarity",
                "kb_name": "cascade-solidarity",
                "entry_type": "solidarity_event",
                "meta": {"infrastructure_types": ["grid"]},
            },
            {
                "id": "priv-solidarity",
                "kb_name": "private-kb",
                "entry_type": "solidarity_event",
                "meta": {"infrastructure_types": ["grid"]},
            },
        ],
    )


class TestCascadeListsNarrowToTheReadableSet:
    def test_actors_serve_their_default_kb_when_it_is_readable(self, db):
        out = _plugin_for(db)._mcp_actors({}, readable_kbs={"cascade-research"})
        assert [a["id"] for a in out["actors"]] == ["pub-actor"]

    def test_actors_serve_nothing_when_the_default_kb_is_not_readable(self, db):
        """The caller may read a KB -- just not the one this tool defaults to."""
        out = _plugin_for(db)._mcp_actors({}, readable_kbs={"cascade-timeline"})
        assert out["actors"] == []

    def test_actors_are_unchanged_for_an_unscoped_caller(self, db):
        out = _plugin_for(db)._mcp_actors({})
        assert [a["id"] for a in out["actors"]] == ["pub-actor"]

    def test_timeline_serves_its_default_kb_only_when_readable(self, db):
        plugin = _plugin_for(db)
        assert [
            e["id"] for e in plugin._mcp_timeline({}, readable_kbs={"cascade-timeline"})["events"]
        ] == ["pub-event"]
        assert plugin._mcp_timeline({}, readable_kbs={"cascade-research"})["events"] == []

    def test_solidarity_timeline_serves_its_default_kb_only_when_readable(self, db):
        plugin = _plugin_for(db)
        readable = plugin._mcp_solidarity_timeline({}, readable_kbs={"cascade-solidarity"})
        assert [e["id"] for e in readable["events"]] == ["pub-solidarity"]
        assert plugin._mcp_solidarity_timeline({}, readable_kbs={"private-kb"})["events"] == []

    def test_infrastructure_types_count_only_readable_rows(self, db):
        plugin = _plugin_for(db)
        readable = plugin._mcp_solidarity_infrastructure_types(
            {}, readable_kbs={"cascade-solidarity"}
        )
        assert readable["infrastructure_types"] == [{"type": "grid", "count": 1}]
        assert (
            plugin._mcp_solidarity_infrastructure_types({}, readable_kbs={"private-kb"})["count"]
            == 0
        )

    def test_capture_lanes_span_only_readable_kbs(self, db):
        """No default here: omitting the name really does span every KB."""
        plugin = _plugin_for(db)
        scoped = plugin._mcp_capture_lanes({}, readable_kbs={"cascade-research"})
        assert scoped["lanes"] == [{"lane": "lane-a", "count": 1}]

        unscoped = plugin._mcp_capture_lanes({})
        assert unscoped["lanes"] == [{"lane": "lane-a", "count": 2}]
