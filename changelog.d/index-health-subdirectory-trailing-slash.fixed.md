- **`pyrite index health` no longer reports a `subdirectory_mismatches` false
  positive for every entry of a type whose declared subdirectory ends in `/`.**
  `people/` and `people` are the same directory, but the check compared the
  declared string against a path component, so a KB created exactly as the
  getting-started guide instructs came back `status: warning` with one row per
  entry. Both sides are normalized now, and an entry genuinely in the wrong
  directory is still flagged (#44).
