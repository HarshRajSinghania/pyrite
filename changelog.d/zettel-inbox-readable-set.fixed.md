- **`zettel_inbox` returns only notes from KBs the caller may read (#223).**
  `kb_name` is optional on the tool, so a call that omitted it read every KB; a
  scoped caller was refused that call outright rather than served the index
  (#201), which left it unusable for exactly the callers it is meant for. The
  handler takes the caller's readable set now and passes it to
  `list_entries(kb_names=...)`, so the storage query narrows rather than the
  page afterwards -- and an empty set matches nothing instead of everything.
  Unscoped callers (global admin, operator API key, local stdio) are unchanged.
