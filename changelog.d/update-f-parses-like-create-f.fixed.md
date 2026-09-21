- **`pyrite update -f` parses its value the same way `create -f` does (#231).**
  The update path coerced ints only, so `-f tags=alpha,beta` wrote the raw
  string; the reader then iterated it as a sequence and tagged the entry with
  the characters of the value, silently dropping it out of tag search,
  `pyrite tags` and every tag-filtered view. Comma-separated lists, JSON arrays
  and objects, floats and booleans now parse identically on both write commands.
