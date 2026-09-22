- **`wiki_stubs`, `wiki_review_queue` and `wiki_quality_stats` return only
  articles from KBs the caller may read (#223).** All three take `kb_name`
  optionally, so a call that omitted it spanned every KB; a scoped caller was
  refused those calls rather than served the index (#201), which left the tools
  unusable for exactly the callers they are meant for. Each passes the caller's
  readable set into the query -- the same `kb_scope_clause` the social tools
  use -- so the lists and counts describe what the caller may read, and an
  empty set matches nothing instead of everything. Unscoped callers (global
  admin, operator API key, local stdio) are unchanged.
