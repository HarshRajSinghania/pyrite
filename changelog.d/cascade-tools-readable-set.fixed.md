- **The cascade list tools return only rows from KBs the caller may read
  (#223).** `cascade_actors`, `cascade_timeline`, `cascade_capture_lanes`,
  `solidarity_timeline` and `solidarity_infrastructure_types` take `kb_name`
  optionally, and four of them default it to their own KB -- so a scoped caller
  who omitted the name was refused rather than served a KB they may not read.
  Each handler passes the caller's readable set to the storage query alongside
  the name, which means the default KB is served only when it is readable, and
  `cascade_capture_lanes` (which has no default) spans exactly what the caller
  may read rather than the whole index. Unscoped callers are unchanged.
