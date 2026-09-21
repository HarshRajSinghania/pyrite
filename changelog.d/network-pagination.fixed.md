- **`cascade_network` and `investigation_network` page both directions instead of
  returning every neighbour at once (#63).** On a hub node the old response was
  roughly 18k tokens (35 outlinks plus about 130 backlinks for one cascade
  node). Both tools now take `limit` (default 50, `0` means no cap) and `offset`
  per direction, order each direction deterministically so a page never repeats
  or skips a row, and return the true totals plus `truncated` so a caller can
  tell what it did not see. The paging lives in `query_network`;
  `get_outlinks` still has no pagination parameters of its own.
