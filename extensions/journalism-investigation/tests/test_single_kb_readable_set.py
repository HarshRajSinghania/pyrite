"""The single-KB investigation tools answer with nothing when the resolved KB
is not readable (#223).

These tools do not span the index: `_resolve_kb` settles on one KB -- the
caller's, or this plugin's default. The MCP chokepoint refuses a call that
*named* an unreadable KB, so the default is the case the guard exists for, and
it is answered with a KB name that matches no entry rather than by inventing an
empty response shape for each of the twelve tools.

The tests avoid hard-coding the plugin's default KB: they resolve it and pass
it back in, so they keep holding if the default changes.
"""

import json
from pathlib import Path

from pyrite_journalism_investigation.plugin import JournalismInvestigationPlugin

from pyrite.storage.database import PyriteDB


def _plugin():
    return JournalismInvestigationPlugin()


class TestReadableKb:
    def test_the_resolved_kb_is_returned_when_the_caller_may_read_it(self):
        plugin = _plugin()
        resolved = plugin._resolve_kb({})
        assert plugin._readable_kb({}, {resolved}) == resolved

    def test_nothing_readable_resolves_to_a_private_guard_name(self):
        assert _plugin()._readable_kb({}, set()).startswith("(unreadable-")

    def test_an_unreadable_default_resolves_to_a_private_guard_name_too(self):
        assert _plugin()._readable_kb({}, {"some-other-kb"}).startswith("(unreadable-")

    def test_each_unreadable_resolution_uses_a_fresh_name(self):
        plugin = _plugin()
        assert plugin._readable_kb({}, set()) != plugin._readable_kb({}, set())

    def test_an_unscoped_caller_keeps_the_resolved_kb(self):
        plugin = _plugin()
        assert plugin._readable_kb({}, None) == plugin._resolve_kb({})

    def test_a_named_readable_kb_resolves_to_itself(self):
        assert _plugin()._readable_kb({"kb_name": "public-kb"}, {"public-kb"}) == "public-kb"


def _make_db(tmp_path, kb, entry_id):
    db = PyriteDB(Path(tmp_path) / "index.db")
    db._raw_conn.execute(
        "INSERT INTO kb (name, path, kb_type) VALUES (?, ?, ?)", (kb, str(tmp_path), "generic")
    )
    db._raw_conn.execute(
        "INSERT INTO entry (id, kb_name, entry_type, title, body, metadata, importance,"
        " created_at, updated_at) VALUES (?, ?, 'investigation_event', ?, '', '{}', 5,"
        " '2026-01-01T00:00:00', '2026-01-01T00:00:00')",
        (entry_id, kb, entry_id),
    )
    db._raw_conn.commit()
    return db


def _plugin_for(db):
    plugin = _plugin()
    plugin._get_db = lambda: (db, False)
    return plugin


class TestTheToolsAnswerWithNothingRatherThanTheDefaultKb:
    def test_timeline_serves_the_default_kb_when_it_is_readable(self, tmp_path):
        resolved = _plugin()._resolve_kb({})
        db = _make_db(tmp_path, resolved, "ev-1")
        try:
            out = json.dumps(_plugin_for(db)._mcp_timeline({}, readable_kbs={resolved}))
        finally:
            db.close()
        assert "ev-1" in out

    def test_timeline_serves_nothing_when_the_default_is_not_readable(self, tmp_path):
        resolved = _plugin()._resolve_kb({})
        db = _make_db(tmp_path, resolved, "ev-1")
        try:
            out = json.dumps(_plugin_for(db)._mcp_timeline({}, readable_kbs={"some-other-kb"}))
        finally:
            db.close()
        assert "ev-1" not in out
        assert out.startswith("{"), "the tool keeps its own response shape"

    def test_a_real_kb_named_like_the_old_guard_is_not_served(self, tmp_path):
        db = _make_db(tmp_path, "(unreadable)", "private-trap")
        try:
            out = json.dumps(_plugin_for(db)._mcp_timeline({}, readable_kbs={"some-other-kb"}))
        finally:
            db.close()
        assert "private-trap" not in out

    def test_an_unscoped_caller_still_sees_the_default_kb(self, tmp_path):
        resolved = _plugin()._resolve_kb({})
        db = _make_db(tmp_path, resolved, "ev-1")
        try:
            out = json.dumps(_plugin_for(db)._mcp_timeline({}))
        finally:
            db.close()
        assert "ev-1" in out
