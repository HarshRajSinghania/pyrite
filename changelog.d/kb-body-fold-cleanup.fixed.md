- **Six backlog files no longer carry a folded copy of their own body, or
  another machine's absolute path (#150).** They were committed with a `body:`
  frontmatter key holding the whole entry text as a YAML scalar, and a stray
  `file_path:` key pointing at a worktree on the machine that wrote them. The
  write path already drops both keys on any save, so every load-and-save
  rewrote those files; they have now been re-saved once, deliberately. The
  text is unchanged -- the body section was already the whole entry, and for
  two of them the folded copy was a truncated prefix of it -- and the
  round-trip gate's residual count drops from 69 to 63.
