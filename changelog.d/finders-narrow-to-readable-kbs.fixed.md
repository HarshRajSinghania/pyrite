- **The four protocol finders narrow to the caller's readable KBs in SQL
  (#223).** `find_by_assignee`, `find_overdue`, `find_by_status` and
  `find_by_location` took a single `kb_name`, so the four `kb_find_by_*` MCP
  tools cut the page with `LIMIT` and dropped unreadable rows afterwards -- a
  scoped caller could receive a short page while readable rows existed below
  the cut. Each finder now takes `kb_names` and narrows through the shared
  `kb_names_clause` (a named KB binds, a readable set narrows, an empty set
  matches nothing, `None` is unchanged), and the four handlers pass the
  readable set down. The handler's post-filter stays as the fail-closed
  guard.
