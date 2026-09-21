"""`pyrite.plugins.scoping.kb_scope_clause` -- the four cases, directly.

The plugin tools that use it are tested through their own handlers; this pins
the contract itself, because six extensions settle on it (#223) and a caller
reading only one of them should not have to infer the rest.
"""

from pyrite.plugins.scoping import kb_scope_clause


def test_a_named_kb_binds_to_that_kb():
    clause, params = kb_scope_clause("kb_name", "private-kb", {"public-kb", "private-kb"})
    assert clause == " AND kb_name = ?"
    assert params == ["private-kb"]


def test_a_readable_set_narrows_to_the_set_in_a_stable_order():
    clause, params = kb_scope_clause("e.kb_name", None, {"b-kb", "a-kb"})
    assert clause == " AND e.kb_name IN (?,?)"
    assert params == ["a-kb", "b-kb"], "sorted, so the SQL text is reproducible"


def test_an_empty_readable_set_matches_nothing_rather_than_everything():
    # `IN ()` is a syntax error, and returning no clause would span the index.
    clause, params = kb_scope_clause("kb_name", None, set())
    assert clause == " AND 1 = 0"
    assert params == []


def test_an_unscoped_caller_gets_no_narrowing_at_all():
    clause, params = kb_scope_clause("kb_name", None, None)
    assert clause == ""
    assert params == []
