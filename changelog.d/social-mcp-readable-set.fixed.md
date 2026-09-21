- **`social_top` and `social_newest` return only writeups from KBs the caller
  may read (#223).** Both take `kb_name` optionally, so a call that omitted it
  read the whole index. A scoped MCP caller was refused those calls rather than
  served the index (#201) -- safe, but it left the tools unusable for exactly
  the callers they are meant for. Each handler takes the readable set now and
  narrows in SQL, so a scoped caller gets a full page of what they may read,
  and a call that names no KB cannot reach a private one. A named KB binds to
  that KB, an empty readable set matches nothing, and an unscoped caller
  (global admin, operator API key, local stdio) is unaffected. This is the
  first of the six extensions; the rest are still listed in
  `OPTIONAL_KB_TOOLS`.
