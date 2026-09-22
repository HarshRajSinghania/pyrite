"""The two cross-KB investigation tools narrow to the caller's readable KBs (#223).

`investigation_search_all` and `investigation_find_duplicates` both accept a
*kb_names* list, and the code they delegate to spells "every KB" as `None` --
so a scoped caller who omitted the list searched the whole index. The handlers
compose what was asked for with what may be read now, and an empty result stays
an empty list rather than collapsing back to `None`, which would search
everything again.
"""

from types import SimpleNamespace

from pyrite_journalism_investigation.plugin import JournalismInvestigationPlugin


def _plugin():
    plugin = JournalismInvestigationPlugin()
    # Neither test reaches a real database: the short-circuit returns first, and
    # the forwarding tests replace the delegated function.
    plugin._get_db = lambda: (SimpleNamespace(), False)
    return plugin


class TestScopedKbNames:
    def test_an_unscoped_caller_keeps_the_request_untouched(self):
        assert _plugin()._scoped_kb_names(["a-kb"], None) == ["a-kb"]
        assert _plugin()._scoped_kb_names(None, None) is None

    def test_omitting_the_list_means_every_readable_kb(self):
        assert _plugin()._scoped_kb_names(None, {"b-kb", "a-kb"}) == ["a-kb", "b-kb"]

    def test_a_request_is_intersected_with_the_readable_set(self):
        assert _plugin()._scoped_kb_names(["a-kb", "private-kb"], {"a-kb"}) == ["a-kb"]

    def test_nothing_readable_is_an_empty_list_not_none(self):
        """`None` is the delegated code's spelling for "every KB", so returning
        it here would search the index for a caller who may read nothing."""
        assert _plugin()._scoped_kb_names(["private-kb"], {"public-kb"}) == []
        assert _plugin()._scoped_kb_names(None, set()) == []


class TestSearchAllForwardsTheNarrowedList:
    def test_the_narrowed_list_reaches_cross_kb_search(self, monkeypatch):
        import pyrite_journalism_investigation.cross_kb_search as mod

        seen = {}

        def fake(db, query, *, kb_names=None, entry_type=None, limit=50):
            seen["kb_names"] = kb_names
            return {"query": query, "total_count": 0, "groups": []}

        monkeypatch.setattr(mod, "cross_kb_search", fake)
        out = _plugin()._mcp_search_all({"query": "zebra"}, readable_kbs={"a-kb"})

        assert seen["kb_names"] == ["a-kb"]
        assert out["total_count"] == 0

    def test_nothing_readable_never_calls_the_search(self, monkeypatch):
        import pyrite_journalism_investigation.cross_kb_search as mod

        def boom(*args, **kwargs):  # pragma: no cover - must not be called
            raise AssertionError("cross_kb_search ran with an empty readable set")

        monkeypatch.setattr(mod, "cross_kb_search", boom)
        out = _plugin()._mcp_search_all({"query": "zebra"}, readable_kbs=set())

        assert out == {"query": "zebra", "total_count": 0, "groups": []}


class TestFindDuplicatesForwardsTheNarrowedList:
    def test_the_narrowed_list_reaches_find_duplicates(self, monkeypatch):
        import pyrite_journalism_investigation.dedup as mod

        seen = {}

        def fake(db, *, kb_names=None, entry_types=None, threshold=0.85):
            seen["kb_names"] = kb_names
            return []

        monkeypatch.setattr(mod, "find_duplicates", fake)
        out = _plugin()._mcp_find_duplicates({}, readable_kbs={"a-kb"})

        assert seen["kb_names"] == ["a-kb"]
        assert out == {"duplicates": []}

    def test_nothing_readable_never_calls_the_scan(self, monkeypatch):
        import pyrite_journalism_investigation.dedup as mod

        def boom(*args, **kwargs):  # pragma: no cover - must not be called
            raise AssertionError("find_duplicates ran with an empty readable set")

        monkeypatch.setattr(mod, "find_duplicates", boom)

        assert _plugin()._mcp_find_duplicates({}, readable_kbs=set()) == {"duplicates": []}
