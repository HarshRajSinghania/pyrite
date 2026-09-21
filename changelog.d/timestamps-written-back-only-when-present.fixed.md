- **`created_at`/`updated_at`: a file that carried them keeps them, a file
  that did not never grows them.** `_base_frontmatter` re-emits the two keys
  only for entries loaded from a file that had them, as second-precision
  timestamps (`updated_at` only when the caller did not supply one); the
  internal stamp goes through `Entry.touch_updated_at()` so bookkeeping is
  not mistaken for a user edit; and unchanged values keep their source node,
  so a `created_at: 2026-01-15` stays a bare date instead of being rewritten
  as a timestamp, and a value the loader cannot parse (`created_at:` with no
  value, `''`, `Jan 15 2026`) is kept exactly as written rather than replaced
  with the load time (#151).
