- **Every `sw_*` read surface returns only rows from KBs the caller may read
  (#223).** Twelve tools in `extensions/software-kb` take `kb_name` optionally
  -- `sw_adrs`, `sw_backlog`, `sw_board`, `sw_component`, `sw_conventions`,
  `sw_create_adr`, `sw_epics`, `sw_milestones`, `sw_pull_next`,
  `sw_review_queue`, `sw_standards`, `sw_validations` -- so a call that omitted
  it spanned every KB, and a scoped caller was refused such calls rather than
  served the index. Each query now narrows through the same `kb_scope_clause`
  the other extensions use: a named KB binds to it, a readable set narrows to
  itself, an empty set matches nothing, and an unscoped caller (global admin,
  operator API key, local stdio) is unchanged.
