"""`?fields=` on the REST read routes keeps the response-required fields (#179).

`GET /api/entries/{id}?fields=title` used to fail with a 500 (response
validation) and `GET /api/search?q=…&fields=title` used to fail with a 400
carrying a raw validation dump, because the projection dropped `id`, `kb_name`,
`entry_type` and `title`, which `EntryResponse` / `SearchResult` require.
"""

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed")

_IDENTITY = {"id", "kb_name", "entry_type", "title"}


def test_get_entry_fields_returns_identity_and_requested(rest_api_env, sample_events):
    client = rest_api_env["client"]
    kb = rest_api_env["events_kb"].name
    entry = sample_events[0]

    resp = client.get(f"/api/entries/{entry.id}?kb={kb}&fields=title")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == entry.id
    assert body["kb_name"] == kb
    assert body["entry_type"] == "event"
    assert body["title"] == entry.title
    assert set(body) == _IDENTITY


def test_get_entry_fields_can_return_a_field_outside_the_model(rest_api_env, sample_events):
    """A requested field the response model does not declare still comes back."""
    client = rest_api_env["client"]
    kb = rest_api_env["events_kb"].name
    entry = sample_events[0]

    resp = client.get(f"/api/entries/{entry.id}?kb={kb}&fields=importance")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["importance"] == entry.importance
    assert _IDENTITY <= set(body)


def test_search_fields_returns_identity_and_requested(rest_api_env):
    client = rest_api_env["client"]

    resp = client.get("/api/search?q=immigration&fields=title")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["results"], body
    for result in body["results"]:
        assert _IDENTITY <= set(result), result
