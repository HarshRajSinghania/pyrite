- **`sw adrs`, `sw components` and `sw standards` are bounded like
  `sw backlog` (#238).** Each returned every matching entry -- no
  `--limit`/`--offset` on the command, no bound on the MCP tool behind it -- so
  on a KB with a few hundred ADRs or components one call could carry the lot
  with no way to page. All six now take the `kb_list_entries` shape: a default
  bound of 50, `--limit 0` (or `limit: null`) for the full list, and `total`,
  `limit`, `offset` and `has_more` on the MCP response. The filter
  (`--status`, `--kind`, `--category`, `path`/`name`) is applied **before** the
  bound, so a filtered page cannot lose a match that sorted past the cut.
