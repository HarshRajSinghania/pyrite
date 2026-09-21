- **The task commands can see a KB that is registered in the database (#245).**
  `kb create` and `kb add` register a KB in the database registry, and every
  other CLI path merges that registry into the config before use. The task
  commands read the YAML config directly, so a registered KB answered
  `KB_NOT_FOUND` from `task create` while `kb list` still showed it — success
  and discoverability both lying about write-readiness. They now go through the
  same shared loader as the rest of the CLI.
