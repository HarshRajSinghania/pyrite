- **The link-discovery routes read every KB a call names, and return
  candidates only from KBs the caller may read (#186).**
  `GET /api/links/discover-neighbors` takes `target_kb` and
  `GET /api/links/batch-suggest` takes `source_kb`/`target_kb`, names the
  per-KB read check in `pyrite/server/api.py` did not look at: a caller could
  name a readable KB and still be served from a private one. Both names are
  resolved like `kb`/`kb_name` now, and
  `LinkDiscoveryService.discover_neighbors`/`batch_suggest` take the caller's
  readable set, so omitting `target_kb` -- which makes the underlying search
  span every KB -- can no longer hand back a private KB's entry as a
  suggestion. The `/mcp` tools `kb_discover_neighbors` and `kb_batch_suggest`
  take the same set, so both surfaces answer alike. Nothing is required of an
  operator.
