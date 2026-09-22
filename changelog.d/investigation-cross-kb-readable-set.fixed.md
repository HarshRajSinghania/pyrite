- **`investigation_search_all` and `investigation_find_duplicates` search only
  the KBs the caller may read (#223).** Both take a *list* of KB names, and
  omitting it means "every KB" to the code they delegate to -- so a scoped
  caller who omitted it searched the whole index. Each handler now composes
  what was asked for with what may be read: a list that names KBs keeps the
  readable ones among them, no list means every readable KB, and an empty
  result stays an empty list rather than collapsing back to "every KB".
  Unscoped callers are unchanged. These were the two genuinely cross-KB tools
  in the last extension; the rest resolve to a single KB and are handled
  separately.
