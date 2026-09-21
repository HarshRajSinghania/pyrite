- **The second, dead `git pull` implementation in `pyrite/github_auth.py` is
  gone, so no unredacted git error text can reach a caller through it (#185).**
  `pull_repo` returned `f"Pull failed: {result.stderr}"` with only the token
  replaced: absolute paths, and whatever else git chose to print, went out
  unredacted, bypassing the path redaction `GitService.sanitize_error` applies.
  Nothing called it — `git grep pull_repo` found only the definition — so there
  is no behaviour change and nothing for an operator to do. A test now pins its
  absence the same way the removed `clone_private_repo` is pinned.
