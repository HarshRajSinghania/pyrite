- **One field-projection rule for every read surface (#193).** `?fields=` on the
  REST routes, the MCP `fields` argument and `--fields` on the CLI now share
  `pyrite/services/read_shaping.py`: the identity pair (`id`, `kb_name`) is kept
  in every projection, keys the record does not have are never invented, and the
  CLI's `--fields` no longer drops the identity pair (that was #192). A
  parametrised test pins the three surfaces to the same key set for the same
  request, which nothing did before.
