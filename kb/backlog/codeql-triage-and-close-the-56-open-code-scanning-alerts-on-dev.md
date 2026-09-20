---
id: codeql-triage-and-close-the-56-open-code-scanning-alerts-on-dev
title: 'CodeQL: triage and close the 47 open code-scanning alerts on dev'
type: backlog_item
tags:
- security
- codeql
- quality
kind: tech_debt
status: proposed
priority: high
effort: M
---

## Problem

GitHub's default CodeQL setup (languages: actions, javascript/typescript, python; weekly + on push) reported **56 open alerts** on `dev` (2026-09-18 10:05Z); the live count is **47** (2026-09-20 — see `## Groom 2026-09-20` §0 for the nine that closed and why). None was triaged; some are certainly noise (a path that is validated by `_validate_entry_id` two frames up still trips `py/path-injection`), some are certainly real (`str(e)` of a subprocess failure returned in an HTTP 500 body), and the page is public. Security-adjacent by definition: **never `good first issue`, always a cold read, Opus for anything that changes a check.**

## Inventory (rule · alert · path:line)

> **STALE — superseded by `## Groom 2026-09-20` §0b.** This is the 2026-09-18 snapshot
> (56 alerts). The eight `actions/missing-workflow-permissions` alerts plus `#35` and
> `#41` are now `fixed`, and line numbers in `git_service.py` and `endpoints/*.py` have
> drifted (PR #161, PR #145) — `#41 git_service.py:102` is now `#57 :212`, and
> `#42 :522` is now `:659`. Rebuild from the API, never from this block.

```
error    py/clear-text-logging-sensitive-data       #10   pyrite/server/mcp_routes.py:182
error    py/clear-text-storage-sensitive-data       #9    scripts/scrape_appointee_details.py:627
error    py/command-line-injection                  #41   pyrite/services/git_service.py:102
error    py/command-line-injection                  #42   pyrite/services/git_service.py:522
error    py/full-ssrf                               #33   pyrite/services/clipper.py:188
error    py/path-injection                          #11   pyrite/server/branding_endpoints.py:61
error    py/path-injection                          #12   pyrite/services/branding_service.py:132
error    py/path-injection                          #13   pyrite/services/branding_service.py:139
error    py/path-injection                          #14   pyrite/services/export_service.py:64
error    py/path-injection                          #15   pyrite/services/export_service.py:69
error    py/path-injection                          #16   pyrite/services/export_service.py:83
error    py/path-injection                          #17   pyrite/services/export_service.py:112
error    py/path-injection                          #18   pyrite/services/export_service.py:161
error    py/path-injection                          #19   pyrite/services/kb_registry_service.py:118
error    py/path-injection                          #20   pyrite/server/static.py:132
error    py/path-injection                          #21   pyrite/server/static.py:138
error    py/path-injection                          #22   pyrite/server/static.py:139
error    py/path-injection                          #23   pyrite/server/static.py:239
error    py/path-injection                          #24   pyrite/server/static.py:245
error    py/path-injection                          #25   pyrite/server/static.py:247
error    py/stack-trace-exposure                    #44   pyrite/server/endpoints/admin.py:136
error    py/stack-trace-exposure                    #45   pyrite/server/endpoints/ai_ep.py:376
error    py/stack-trace-exposure                    #46   pyrite/server/endpoints/entries.py:597
error    py/stack-trace-exposure                    #47   pyrite/server/endpoints/git_ops.py:39
error    py/stack-trace-exposure                    #48   pyrite/server/endpoints/git_ops.py:61
error    py/stack-trace-exposure                    #49   pyrite/server/endpoints/git_ops.py:82
error    py/stack-trace-exposure                    #50   pyrite/server/endpoints/kbs.py:182
error    py/stack-trace-exposure                    #51   pyrite/server/endpoints/repos.py:79
error    py/stack-trace-exposure                    #52   pyrite/server/endpoints/repos.py:103
error    py/stack-trace-exposure                    #53   pyrite/server/endpoints/repos.py:224
error    py/stack-trace-exposure                    #54   pyrite/server/endpoints/worktree.py:176
error    py/stack-trace-exposure                    #55   pyrite/server/endpoints/worktree.py:184
error    py/stack-trace-exposure                    #56   pyrite/server/endpoints/worktree.py:303
warning  actions/missing-workflow-permissions       #1    .github/workflows/ci.yml:28
warning  actions/missing-workflow-permissions       #2    .github/workflows/ci.yml:57
warning  actions/missing-workflow-permissions       #3    .github/workflows/ci.yml:78
warning  actions/missing-workflow-permissions       #4    .github/workflows/ci.yml:199
warning  actions/missing-workflow-permissions       #5    .github/workflows/ci.yml:232
warning  actions/missing-workflow-permissions       #6    .github/workflows/ci.yml:271
warning  actions/missing-workflow-permissions       #7    .github/workflows/ci.yml:366
warning  actions/missing-workflow-permissions       #8    .github/workflows/ci.yml:424
warning  py/incomplete-url-substring-sanitization   #34   pyrite/config.py:155
warning  py/incomplete-url-substring-sanitization   #35   pyrite/github_auth.py:363
warning  py/incomplete-url-substring-sanitization   #36   tests/test_git_service.py:50
warning  py/incomplete-url-substring-sanitization   #37   tests/test_llm_service.py:186
warning  py/incomplete-url-substring-sanitization   #38   tests/test_llm_service.py:191
warning  py/incomplete-url-substring-sanitization   #39   tests/test_notebooklm_renderer.py:254
warning  py/incomplete-url-substring-sanitization   #40   pyrite/services/user_service.py:83
warning  py/polynomial-redos                        #43   pyrite/services/search_service.py:98
warning  py/weak-sensitive-data-hashing             #26   pyrite/server/api.py:392
warning  py/weak-sensitive-data-hashing             #27   pyrite/server/api.py:400
warning  py/weak-sensitive-data-hashing             #28   pyrite/server/api.py:401
warning  py/weak-sensitive-data-hashing             #29   tests/e2e/conftest.py:253
warning  py/weak-sensitive-data-hashing             #30   pyrite/server/mcp_routes.py:67
warning  py/weak-sensitive-data-hashing             #31   pyrite/server/mcp_routes.py:110
warning  py/weak-sensitive-data-hashing             #32   pyrite/server/mcp_routes.py:118
```

## What the spike must produce (written into this item as `## Groom`)

For each rule group: (1) true positive or noise, with the reasoning per alert (which sanitizer/validator, if any, sits on the data path — `_validate_entry_id`, `_contained`, the auth tier); (2) for the true positives, the exploit shape against the REST/MCP surface as deployed (which tier can reach it, what it yields); (3) themes a worker can execute — acceptance criteria, footprint, model, cold read (always yes), sequence against the themes in flight (`pyrite/server/endpoints/*`, `git_service.py`, `clipper.py`, `static.py`, `config.py`); (4) for the noise, the CodeQL dismissal reason per alert (`false positive` / `won't fix` / `used in tests`) so the conductor can dismiss them through the API with a comment, not silently. The `actions/missing-workflow-permissions` group (8) is already a separate Sonnet theme (`fix/workflow-permissions`) and is out of the spike's scope.

## Rule groups

- `py/stack-trace-exposure` ×13 (error) — `endpoints/{admin,ai_ep,entries,git_ops,kbs,repos,worktree}.py`: exception text or traceback reaching a response body.
- `py/path-injection` ×15 (error) — `branding_endpoints.py`, `branding_service.py`, `export_service.py`, `kb_registry_service.py`, `server/static.py` (6 in the static file server).
- `py/command-line-injection` ×2 (error) — `git_service.py:102, :522`.
- `py/full-ssrf` ×1 (error) — `clipper.py:188` (the backlog item `web-clipper-response-size-cap-and-dns-rebinding-toctou-defense` already covers part of this).
- `py/clear-text-logging-sensitive-data` ×1 (error) — `mcp_routes.py:182` (a password logged); `py/clear-text-storage-sensitive-data` ×1 — `scripts/scrape_appointee_details.py:627` (a script, not the product).
- `py/weak-sensitive-data-hashing` ×7 (warning) — `server/api.py:392–401`, `mcp_routes.py:67–118`, `tests/e2e/conftest.py:253` — API-key hashing; decide whether sha256 of a high-entropy key is the intended design (then dismiss with the reason) or whether a keyed hash is warranted.
- `py/incomplete-url-substring-sanitization` ×7 (warning) — `config.py:155`, `github_auth.py:363`, `user_service.py:83`, three tests.
- `py/polynomial-redos` ×1 (warning) — `search_service.py:98`.

## Also for the maintainer (kept)

Whether CodeQL should become a required PR check (a repo setting) once the count is at zero-or-dismissed; today it runs but does not gate.

## Groom 2026-09-18

> **Partly superseded by `## Groom 2026-09-20`.** Its per-alert reasoning mostly stands and
> is cited there, but its counts, line numbers and dismissal table are stale: Theme B is
> **done** (PR #161), Theme C1 is **void** (#35 is `fixed`), alert #33 must **not** be
> dismissed (issue #219), and one alert it called noise (#16 `export_service.py:83`) is a
> true positive. Read the 09-20 section first.

Spike: `spike/codeql-triage` (worktree discarded, no code committed). Evidence is
from reading `origin/dev` plus four throwaway experiments: a `TestClient` repro of
the search endpoint, a direct-call probe of `static.py`'s containment checks, a
probe of `sanitize_filename`, and a timing comparison of two candidate ReDoS fixes.

**Counts (48 alerts in scope; the 8 `actions/missing-workflow-permissions` are excluded):**

| Verdict | Count |
|---|---|
| True positive | 4 |
| Noise (dismiss) | 43 |
| Needs a maintainer decision | 1 (`py/weak-sensitive-data-hashing`, recommendation below) |

The headline finding is that **exactly one alert is remotely exploitable**, and it
is not one of the 33 `error`-severity ones: `py/polynomial-redos` #43 (a `warning`)
is a reproduced read-tier denial of service. The 15 `py/path-injection` and 13
`py/stack-trace-exposure` `error` alerts are, with three exceptions, guarded.

---

### 1. Per-alert verdicts

#### `py/polynomial-redos` #43 — `search_service.py:98` — **TRUE POSITIVE (the only exploitable one)**

No sanitizer. `sanitize_fts_query` applies `re.sub(r"(\S*[^\w\s]\S*)", ...)` to the
raw `q` query parameter. The two `\S*` around the character class make the match
quadratic in the length of a single non-space run. `GET /api/search` declares
`q: str = Query(..., min_length=1)` — **no `max_length`** — so the run is caller-controlled
and unbounded.

Reproduced end to end through `TestClient` against `create_app()` (`rest_api_env`):

```
baseline  q=hello           200     30.0 ms
q = "a" *  5000             200    143.5 ms
q = "a" * 20000             200   2838.6 ms
q = "a" * 40000             200  12254.3 ms
```

Direct timing of the regex alone, off the request path: n=50000 → 10.2 s, n=100000 → 40.2 s,
n=400000 → **773 s** (nearly 13 minutes of CPU for one request). The growth is quadratic,
confirming the rule.

**Exploit shape.** Tier: **read** — the route is `dependencies=[Depends(requires_kb_read())]`,
so any read key, or any anonymous caller on a deployment with `default_role: read` or
`PYRITE_AUTH_ANONYMOUS_TIER=read`, reaches it. Rate limit is `100/minute`. At ~12 s of
single-threaded CPU per request, well under 100 requests/minute saturates every worker;
the yield is a full denial of service of the whole API process, not just search.
The same sanitizer is on the MCP `search` path via `search_service.py:270` and `:388`,
so the MCP read tier reaches it too.

**The fix is a length cap, not a regex rewrite.** I tried the obvious rewrite
`(?=\S*[^\w\s])(\S+)`. It produces byte-identical output on every sanitizer test case, and
it is *also* quadratic — **and at the lengths that matter it is far worse than what it
replaces**:

```
n        original      lookahead rewrite
5000       0.11 s       0.10 s
20000      1.62 s       1.60 s
100000    40.2 s      295.1 s      <- 7.3x WORSE
400000   773.1 s     1021.8 s
```

Below ~20k the two are indistinguishable, which is exactly the trap: a worker who measures
only short inputs will conclude the rewrite helps. It does not — it makes the attack
cheaper. Truncating the query to 512 characters before the `re.sub` bounds the worst case
at **1.497 ms** and leaves all six sanitizer behaviours byte-identical.

#### `py/stack-trace-exposure` ×13 — **1 true positive, 2 partial, 10 noise**

CodeQL's "stack trace information" here is `str(e)` of a caught exception, never a
formatted traceback: no `traceback.format_exc()`, `repr(e)` of a chained exception, or
`debug=True` handler exists on any of these paths. I checked each body by calling it.

- **#51 `repos.py:79` — TRUE POSITIVE (information disclosure, not a traceback).**
  `POST /api/repos/subscribe` returns `result["error"]`, which is `GitService.clone`'s
  `f"Clone failed: {error}"` carrying raw git stderr. Reproduced:
  ```
  POST /api/repos/subscribe {"remote_url":"https://github.com/does-not-exist-zzz/nope"}
  400 {"detail":{"code":"SUBSCRIBE_FAILED","message":"Clone failed: Cloning into
      '/Users/markr/.pyrite/repos/does-not-exist-zzz/nope'...\nremote: Repository not
      found.\nfatal: repository 'https://github.com/...' not found\n"}}
  ```
  Tier: **write** (`repos.py` router carries `dependencies=[Depends(requires_tier("write"))]`).
  Yield: the server's absolute filesystem layout (`$HOME`, the workspace root) and raw
  git stderr. `_sanitize_output` already strips the OAuth token, so no credential leaks —
  but the path disclosure is real and feeds path-guessing against other surfaces.
  Note this also confirms an existence oracle: a write-tier caller learns whether an
  arbitrary private GitHub repo exists, via the operator's stored token.
- **#52 `repos.py:103`, #53 `repos.py:224` — PARTIAL, same shape, lower yield.**
  `fork_and_subscribe` / `create_pr` return `result["error"]`, which is GitHub API error
  text rather than local paths. Same write tier. Fix them with #51 in one pass; on their
  own they would be "won't fix".
- **#47/#48/#49 `git_ops.py:39,61,82` — NOISE.** Admin tier
  (`dependencies=[Depends(requires_tier("admin"))]` on each route) and the message is a
  curated `PyriteError` string, not an exception chain. Verified:
  `POST /api/kbs/test-events/commit` → `400 {"code":"COMMIT_FAILED","message":"KB
  'test-events' is not in a git repository"}`. Nothing internal escapes.
- **#50 `kbs.py:182` — NOISE.** `export_kb_to_repo`'s errors are `KBNotFoundError` /
  curated `{"success": false, "error": ...}` dicts; the git stderr path here goes through
  `GitService.clone`'s `_sanitize_output` and the endpoint is admin-gated.
- **#54/#55/#56 `worktree.py:176,184,303` — NOISE.** The flagged value is
  `GitService.diff_branches`'s failure message returned as `{"error": diff}`. Both routes
  require `request.state.auth_user` (401 otherwise); the content is a git diff the caller
  is already authorised to read. `diff_branches` output is the diff, not an exception.
- **#44 `admin.py:136` — NOISE.** `llm.test_connection()`'s return dict. Write tier, and
  the endpoint's entire purpose is to report why the operator's own AI provider call
  failed. Suppressing it would remove the feature.
- **#45 `ai_ep.py:376` — NOISE.** `str(e)` into an SSE `{"type":"error"}` frame on the
  operator's own LLM stream, with `logger.exception` beside it. Same argument as #44:
  the message is the product.
- **#46 `entries.py:597` — NOISE.** Per-row `{"title": ..., "error": str(e)}` in a bulk
  import result. The caller supplied the rows; the error describes the caller's own input.

#### `py/path-injection` ×15 — **all 15 NOISE**

Every one has a containment check or a registry lookup on the path. I verified the two
that actually take a URL path segment by calling them directly.

- **#20–#25 `static.py:132,138,139,239,245,247` — NOISE, `_contained`-style guard verified.**
  `_serve_static_dir` and `_serve_site_cached` both do
  `resolved = file_path.resolve()` then `if not resolved.is_relative_to(directory.resolve()): return 404`,
  inside `try/except (ValueError, OSError)`. Probed against a real temp tree with a
  sibling `SECRET.html`:
  ```
  '../SECRET.html'              -> 404
  '..%2fSECRET.html'            -> 404
  'inside/../../SECRET.html'    -> 404
  '/etc/hosts'                  -> 404
  'inside/ok.html' (legit)      -> served
  symlink inside -> ../SECRET   -> 404   (resolve() follows the link, containment catches it)
  ```
  CodeQL flags line 132 (`.resolve()`) and 138/139 (`.is_file()` / `FileResponse`) because
  it does not model `is_relative_to` as a barrier. The symlink case is the one that would
  break a naive `os.path.normpath` guard, and this code survives it.
- **#11 `branding_endpoints.py:61` + #12/#13 `branding_service.py:132,139` — NOISE.**
  Same pattern: `resolve_asset` builds `(self._branding_dir / filename).resolve()` then
  `candidate.relative_to(base)` in a `try/except ValueError` that logs
  `"Asset traversal attempt rejected"` and returns `None`, and the endpoint 404s on `None`.
  The guard is the `relative_to` call CodeQL steps over.
- **#14–#18 `export_service.py:64,69,83,112,161` — NOISE.** The tainted value is `kb_name`,
  and `self.config.get_kb(kb_name)` is a **dict lookup** against the registered KB map
  (`self._kb_by_name.get(name)` / `self._db_kb_cache.get(name)`), returning `None` →
  `KBNotFoundError` for anything not already registered. A traversal string is simply not
  a key. Separately, #17's per-entry filename goes through `sanitize_filename`, verified:
  ```
  '../../etc/passwd'        -> '_etc_passwd'
  '....//....//etc/passwd'  -> '_etc_passwd'
  '/etc/passwd'             -> '_etc_passwd'
  'a/../../b'               -> 'a_b'
  ```
- **#19 `kb_registry_service.py:118` — NOISE (by design, and admin-gated).** `add_kb` does
  `Path(path).expanduser().resolve()` and `mkdir(parents=True)` on an operator-supplied
  path. That *is* the feature — registering a KB at an arbitrary filesystem location — and
  the only route to it, `POST /api/kbs` in `admin.py:196`, carries `requires_tier("admin")`.
  An admin already has the KB registry; there is no privilege boundary to cross.

#### `py/command-line-injection` ×2 — **both NOISE**

- **#41 `git_service.py:102` (`clone`) — NOISE, three guards.** (a) `remote_url` reaches
  `clone` from `repo_service.subscribe` only after `GitService.parse_github_url`, which
  does real `urlparse`, requires `scheme == "https"` (or the exact `git@github.com:` SSH
  prefix), requires the host to *equal* `github.com`, and matches both owner and repo
  against `_GITHUB_NAME_RE.fullmatch`. (b) `clone` itself refuses any `remote_url` or
  `branch` starting with `-`, with a comment naming `--upload-pack=<cmd>` as the reason —
  someone already thought about this. (c) the argv is a list with `--` before the
  positionals, and `shell=False`. Argument injection is closed on all three counts.
- **#42 `git_service.py:522` (`commit`) — NOISE.** `git add -- <p>` uses `--` and a list
  argv; `git commit -m <message>` passes the message as an argument value, not a flag
  position. Admin tier (`git_ops.py` commit route). No shell.

#### `py/full-ssrf` #33 — `clipper.py:188` — **NOISE (a known, documented residual)**

`clip_url` calls `_check_url_safe(url)` **before** any HTTP request. It rejects non-http(s)
schemes, hostless URLs, IP literals in loopback/link-local/private/reserved/unspecified/
multicast ranges, and — after `getaddrinfo` — rejects if *any* resolved address is blocked
(closing the mixed public/private A-record trick). CodeQL does not model it. The residual
that remains is DNS rebinding between the check and the connect, which is *already*
tracked by the backlog item `clipper-ssrf-defense-followups` and named in the docstring.
Dismissing #33 does not lose that work; it is ticketed elsewhere.

#### `py/clear-text-logging-sensitive-data` #10 — `mcp_routes.py:182` — **NOISE**

The alert points at columns 71–75 of
`logger.info("MCP SSE connection: user=%s tier=%s", client_id, tier)` — i.e. **`tier`**.
CodeQL types the API key as a "password", taints `role` through `_resolve_api_key_role`,
and follows it into `tier`. But `tier` is one of the three literals `"read"`, `"write"`,
`"admin"`, and `client_id` is `f"apikey-{sha256(key)[:8]}"`. The key never reaches the log.
This is a textbook taint-label false positive.

#### `py/clear-text-storage-sensitive-data` #9 — `scripts/scrape_appointee_details.py:627` — **NOISE**

`person_path.write_text(new_text)` in a one-off scraper for **published** ProPublica
financial-disclosure data. CodeQL matched on the local name `private`. Not shipped in the
package, not on any request path.

#### `py/incomplete-url-substring-sanitization` ×7 — **all NOISE, two worth a code comment**

- **#34 `config.py:155` — NOISE.** `"github.com" in self.remote` inside `is_github`, used
  only to decide whether the `github_oauth` auth method is *configurable* for a repo the
  operator wrote into `config.yaml`. It gates a validation warning, not a credential.
- **#35 `github_auth.py:363` — NOISE, but the *pattern* is the one already fixed elsewhere.**
  `if "github.com" in repo_url:` then inject the token into the URL. That substring check
  would match `https://github.com.evil.tld/...`. It is noise **today** only because this
  function is CLI-only (`get_github_token()` reads the local gh/keyring token) and
  `repo_url` is operator-typed, never request-derived. The server path already does this
  correctly — `GitService._github_repo_path` exists precisely because, in its own words,
  the old substring test "also matches strings and fragments -- and `_inject_token` trusted
  that match enough to hand over the caller's OAuth token." Dismiss as false positive, but
  the worker should route this call through `_github_repo_path` for consistency while it is
  in the file (see Theme C).
- **#40 `user_service.py:83` — NOISE.** `"noreply.github.com" in email` is a heuristic for
  parsing `12345+login@users.noreply.github.com`; the result is only used to look up an
  *already-existing* user row (`self.db.get_user(github_login=login)`), which returns `None`
  for a forged value. No account is created and no trust is granted from the substring.
- **#36 `tests/test_git_service.py:50`, #37/#38 `tests/test_llm_service.py:186,191`,
  #39 `tests/test_notebooklm_renderer.py:254` — NOISE, test assertions.** Dismiss as
  `used in tests`.

#### `py/weak-sensitive-data-hashing` ×7 — **NEEDS A DECISION (recommendation: dismiss, with one doc change)**

Sites: `api.py:392,400,401`, `mcp_routes.py:67,110,118`, `tests/e2e/conftest.py:253`.
All are `hashlib.sha256(key.encode()).hexdigest()` compared with
`secrets.compare_digest` against a stored `key_hash`.

The rule's own text is the tell: *"insecure for **password** hashing, since it is not a
computationally expensive hash function."* That argument applies to a **low-entropy
human-chosen secret**, where an attacker who steals the hash file brute-forces the
preimage offline. It does not apply to a high-entropy random token, where the search space
defeats any number of hashes per second. The comparison is already constant-time, so
timing is closed.

**But Pyrite does not currently guarantee the key is high-entropy.** There is no
`pyrite key new` command; `docs/configuration.md` tells the operator to put
`key_hash: "<sha256 of the key>"` in `config.yaml` and says nothing about how to choose
the key. An operator who picks `hunter2` gets a sha256 that falls to a wordlist in
milliseconds. The session-token path does it right (`secrets.token_urlsafe(32)` in
`auth_service.py:579`); the API-key path leaves it to the human.

**Recommendation — dismiss all 7 as `won't fix`, and close the gap with documentation and
a mint command rather than a keyed hash.** Reasoning: HMAC or Argon2 here would buy
nothing against a *random* key and would be a breaking change to every deployed
`config.yaml`; the actual risk is a weak operator-chosen key, which a keyed hash does not
fix either (the server key sits in the same file). Making the key generator the documented
path removes the premise. This is a recommendation, not a decision — see "Also for the
maintainer" below; Theme D is written so it can be dispatched either way.

`tests/e2e/conftest.py:253` is `used in tests` regardless of the outcome.

---

### 2. Themes

Sequencing note: `pyrite/server/endpoints/*` is quiet right now. `search_service.py` and
`endpoints/search.py` are both in PR #145's review (which also touches `mcp_server.py`),
so **Theme A must wait for #145 to land**. `mcp_server.py` will be touched by 7D/7E, but
no theme here touches it.

**Cold read: yes for all four themes. `heavy: no` for all four.**

---

#### Theme A — `fix/search-query-length-cap` — the ReDoS

**Model: opus** (it changes a guard on the read tier and must not change sanitizer output).
**Sequence: after PR #145 merges** — hard conflict on `search_service.py` and
`endpoints/search.py`.

Touches (existing): `pyrite/services/search_service.py`, `pyrite/server/endpoints/search.py`,
`pyrite/server/tool_schemas.py` (the MCP `search` tool's query schema), `CHANGELOG.md`.
Touches (new): `tests/test_search_query_length_cap.py`.

Acceptance criteria:
1. `SearchService.sanitize_fts_query` truncates its input to a module-level
   `MAX_FTS_QUERY_CHARS = 512` before the `re.sub`. The cap is applied in
   `sanitize_fts_query` itself, not only at the endpoint — `search_service.py:270` and
   `:388` are both call sites and the MCP path reaches them.
2. `GET /api/search` declares `q: str = Query(..., min_length=1, max_length=512)`, so an
   over-long query is rejected with a 422 naming the limit rather than silently truncated
   at the HTTP edge.
3. The MCP `search` tool's `query` property in `tool_schemas.py` carries the same
   `maxLength: 512`.
4. A test asserts `sanitize_fts_query("a" * 100_000)` completes in under 100 ms. (Measured
   headroom: the capped call is ~1.5 ms; the uncapped one is ~41 s at that length. Use a
   wall-clock budget generous enough to survive `-n auto`, per the pre-push rule — 100 ms
   against a 1.5 ms actual is ~65x headroom.)
5. A test asserts the six sanitizer behaviours are unchanged by the cap, at minimum:
   `"alex-jones"` → `'"alex-jones"'`; `"0.6 milestone"` → `'"0.6" milestone'`;
   `"alex jones"` unchanged; `'alex AND "not-here"'` unchanged (operator short-circuit);
   `"a-b c.d ef"` → `'"a-b" "c.d" ef'`; `"foo_bar baz-qux"` → `'foo_bar "baz-qux"'`.
6. A `TestClient` test asserts `GET /api/search?q=<600 chars>` returns 422, and
   `?q=<512 chars>` returns 200.
7. **Do not "fix" the regex.** The rewrite `(?=\S*[^\w\s])(\S+)` is byte-identical on
   output, still quadratic, and **7.3x slower than the original at n=100000** (295 s vs
   40 s) — it makes the attack cheaper, not dearer. It looks equivalent below ~20k, so
   benchmarking short inputs will mislead you. A reviewer seeing a regex change instead of
   a cap should reject the branch.

Evidence the worker can copy: the `TestClient` timing repro in section 1 is four lines
against the `rest_api_env` fixture and belongs in the new test file as criterion 4/6.

---

#### Theme B — `fix/repo-error-message-disclosure` — git stderr and absolute paths in 400 bodies

**Model: opus** (it decides what an error may say; getting it wrong either leaks or makes
the feature undiagnosable). **Sequence: now** — `endpoints/repos.py` and
`services/git_service.py` are quiet; no open PR touches either.

Touches (existing): `pyrite/services/git_service.py` (a new sanitiser beside the existing
`_sanitize_output`), `pyrite/server/endpoints/repos.py`, `pyrite/services/repo_service.py`,
`CHANGELOG.md`. Touches (new): `tests/test_repo_error_disclosure.py`.

Acceptance criteria:
1. `GitService` gains a path-redacting step applied to every message returned to a caller:
   any absolute filesystem path in git stderr is replaced with a stable placeholder
   (e.g. `<workspace>/owner/repo`). Keep the existing token redaction in `_sanitize_output`;
   this is additive, not a replacement.
2. `POST /api/repos/subscribe` against a non-existent repo returns a 400 whose
   `detail.message` contains **no** substring of the server's `$HOME` or workspace root,
   and no `Cloning into '...'` line. The reproduced string in section 1 is the exact
   regression case; assert on it.
3. The message still distinguishes the three failures a write-tier caller must act on:
   repository not found / authentication required / branch not found. A test asserts each
   maps to a distinct, stable `code` in the detail body. Collapsing all three into
   "Clone failed" is a regression, not a fix.
4. The full stderr is still `logger.warning`'d server-side, so the operator loses nothing.
   A test asserts the log record contains what the response body omits.
5. `POST /api/repos/fork` (#52) and `POST /api/repos/{name}/pr` (#53) route their
   `result["error"]` through the same sanitiser.
6. Existing tests in `tests/test_rest_api.py` and any repo-service tests still pass
   unchanged, or their changed assertions are justified in the commit message.

Out of scope, name it in the PR body and do not chase it: the private-repo existence
oracle noted under #51. It is inherent to letting a write-tier caller clone through the
operator's token, and needs a design decision rather than a message change.

---

#### Theme C — `chore/codeql-dismissals-and-substring-host-checks` — the noise, closed out

**Model: opus** (43 dismissals each need the right reason recorded, and one of them is a
"noise today, would be a vulnerability if this function ever took request input" case).
**Sequence: now**, but **after** Themes A and B have merged, so the two true positives are
fixed before the remaining alerts are dismissed and the page reads honestly.

Touches (existing): `pyrite/github_auth.py` (route line 363 through
`GitService._github_repo_path` instead of `"github.com" in repo_url`),
`pyrite/services/user_service.py` (a comment at line 83 naming why the substring check is
safe here — the lookup-only use), `pyrite/config.py` (same, at `is_github`),
`pyrite/server/mcp_routes.py` (a comment at line 182 naming that only the tier literal and
a truncated hash are logged, so the next reader does not "fix" it by removing the log).
Touches (new): none.

Acceptance criteria:
1. `github_auth.py`'s token injection no longer decides on `"github.com" in repo_url`. It
   uses the same host-equality check the server path uses. A test asserts that
   `https://github.com.evil.tld/a/b` does **not** get the token injected — this is the
   regression `_github_repo_path`'s docstring already describes for the server path.
2. No behaviour change to `config.py:155` or `user_service.py:83` — comments only.
3. The dismissals themselves are **not** in this PR; they are API calls the conductor makes
   (table below). The PR body lists the alert numbers it makes dismissible.

---

#### Theme D — `docs/api-key-entropy` — only if the maintainer chooses "dismiss"

**Model: sonnet** (documentation plus one small, well-specified command).
**Sequence: after the maintainer's decision on `py/weak-sensitive-data-hashing`.** Do not
dispatch before then; if the decision is "keyed hash", this theme is replaced by a
different one and must be re-groomed (a keyed hash is a breaking `config.yaml` change and
would need its own ADR).

Touches (existing): `docs/configuration.md`, `pyrite/cli/` (a new `pyrite key new`
subcommand), `CHANGELOG.md`. Touches (new): `tests/test_key_mint_command.py`.

Acceptance criteria:
1. `pyrite key new [--role read|write|admin] [--label X]` prints a
   `secrets.token_urlsafe(32)` key **once**, plus the `config.yaml` stanza containing only
   its sha256. It never writes the plaintext to disk or to the log.
2. `docs/configuration.md`'s `api_keys` section leads with that command and states
   explicitly that the sha256 is safe **because** the key is high-entropy and random, and
   that a hand-chosen key is not supported.
3. A test asserts the minted key is at least 32 bytes of entropy and that two successive
   invocations differ.
4. No change to the verification path in `api.py` or `mcp_routes.py`.

---

### 3. Dismissal table (43 alerts) — for the conductor's API calls

`gh api -X PATCH repos/markramm/pyrite/code-scanning/alerts/<n> -f state=dismissed
-f dismissed_reason='<reason>' -f dismissed_comment='<one line>'`

Dismiss **after** Themes A and B merge.

| # | Rule | Reason | Comment |
|---|---|---|---|
| 9 | clear-text-storage | `won't fix` | One-off scraper for published ProPublica disclosures; matched on the local name `private`. Not in the package, not on a request path. |
| 10 | clear-text-logging | `false positive` | The flagged columns are `tier`, one of the literals read/write/admin. `client_id` is a truncated sha256. The key never reaches the log. |
| 11 | path-injection | `false positive` | `resolve_asset` enforces `candidate.relative_to(branding_dir)` and 404s on ValueError. Traversal and symlink escape both verified rejected. |
| 12 | path-injection | `false positive` | Same `relative_to` containment guard; CodeQL does not model it as a barrier. |
| 13 | path-injection | `false positive` | Same `relative_to` containment guard. |
| 14 | path-injection | `false positive` | `kb_name` is a dict-lookup key into the registered-KB map; an unregistered value raises KBNotFoundError before any path use. |
| 15 | path-injection | `false positive` | Same registry-lookup barrier on `kb_name`. |
| 16 | path-injection | `false positive` | Same registry-lookup barrier on `kb_name`. |
| 17 | path-injection | `false positive` | Entry filename goes through `sanitize_filename`; `../../etc/passwd` → `_etc_passwd`, verified. |
| 18 | path-injection | `false positive` | Same registry-lookup barrier on `kb_name`. |
| 19 | path-injection | `won't fix` | Registering a KB at an operator-chosen path is the feature; the only route is `POST /api/kbs`, admin tier. No boundary crossed. |
| 20 | path-injection | `false positive` | `_serve_static_dir` enforces `resolved.is_relative_to(directory.resolve())`; `../`, encoded, nested and symlink escapes all verified 404. |
| 21 | path-injection | `false positive` | Same containment guard in `_serve_static_dir`. |
| 22 | path-injection | `false positive` | Same containment guard in `_serve_static_dir`. |
| 23 | path-injection | `false positive` | `_serve_site_cached` enforces the same `is_relative_to` containment; verified 404 on traversal. |
| 24 | path-injection | `false positive` | Same containment guard in `_serve_site_cached`. |
| 25 | path-injection | `false positive` | Same containment guard in `_serve_site_cached`. |
| 26 | weak-hashing | `won't fix` | sha256 of a high-entropy random API key, compared with `compare_digest`. The rule's premise is offline brute force of a low-entropy password. See Theme D. |
| 27 | weak-hashing | `won't fix` | Same: sha256 of a high-entropy random API key with constant-time comparison. |
| 28 | weak-hashing | `won't fix` | Same: sha256 of a high-entropy random API key with constant-time comparison. |
| 29 | weak-hashing | `used in tests` | e2e test fixture minting a throwaway key. |
| 30 | weak-hashing | `won't fix` | Same as #26, on the MCP auth path. |
| 31 | weak-hashing | `won't fix` | Same as #26, on the MCP auth path. |
| 32 | weak-hashing | `won't fix` | Same as #26, on the MCP auth path. |
| 33 | full-ssrf | `false positive` | `_check_url_safe` runs before any request: scheme allowlist, IP-literal check, and rejection if *any* resolved address is private/loopback/reserved. Residual DNS-rebinding risk is tracked in `clipper-ssrf-defense-followups`. |
| 34 | incomplete-url-sanitization | `false positive` | `is_github` gates a config-validation warning for an operator-written remote; no credential decision. |
| 35 | incomplete-url-sanitization | `false positive` | CLI-only path with an operator-typed URL; hardened anyway in Theme C to use host equality. |
| 36 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 37 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 38 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 39 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 40 | incomplete-url-sanitization | `false positive` | The parsed login is only used to look up an existing user row; a forged value returns None. No account creation, no trust granted. |
| 41 | command-line-injection | `false positive` | `parse_github_url` enforces https + host equality + `_GITHUB_NAME_RE.fullmatch`; `clone` refuses leading `-` on url and branch; list argv with `--` and `shell=False`. |
| 42 | command-line-injection | `false positive` | List argv with `--` before positionals, `shell=False`, admin tier. |
| 44 | stack-trace-exposure | `won't fix` | `llm.test_connection()`'s diagnostic is the endpoint's purpose; write tier, operator's own provider. |
| 45 | stack-trace-exposure | `won't fix` | `str(e)` in an SSE error frame on the operator's own LLM stream; `logger.exception` beside it. |
| 46 | stack-trace-exposure | `won't fix` | Per-row import error describing the caller's own submitted row. |
| 47 | stack-trace-exposure | `false positive` | Admin tier; the body is a curated `PyriteError` message ("KB 'x' is not in a git repository"), not an exception chain. Verified by calling it. |
| 48 | stack-trace-exposure | `false positive` | Same: admin tier, curated PUBLISH_FAILED message. |
| 49 | stack-trace-exposure | `false positive` | Same: admin tier, curated COMMIT_FAILED message. Verified. |
| 50 | stack-trace-exposure | `false positive` | Admin tier; errors are KBNotFoundError or curated dicts, and git stderr passes `_sanitize_output`. |
| 54 | stack-trace-exposure | `false positive` | Requires `auth_user` (401 otherwise); the value is a git diff the caller is authorised to read, not an exception. |
| 55 | stack-trace-exposure | `false positive` | Same: authenticated worktree diff content. |
| 56 | stack-trace-exposure | `false positive` | Same: authenticated worktree diff content. |

Alerts **43, 51, 52, 53** are the true positives and must be closed **by a fix** (Themes A
and B), never dismissed. They should go to `fixed` on their own when the branches land.

---

### 4. Also for the maintainer (kept)

Two decisions, both stated as recommendations only:

1. **`py/weak-sensitive-data-hashing` (7 alerts).** Recommendation: **dismiss as
   `won't fix`** and dispatch Theme D (mint command + docs), rather than moving to a keyed
   hash. A keyed hash buys nothing against a random 32-byte key and breaks every deployed
   `config.yaml`; the real gap is that nothing today *makes* the key random. If you prefer
   the keyed hash, Theme D is void and the change needs an ADR — say so and it will be
   re-groomed.
2. **CodeQL as a required check** (already on this ticket). Worth noting from the spike:
   of 48 alerts, 44 were noise. Making the current rule set blocking would have gated the
   repo on false positives roughly ten times more often than on real ones. If it becomes
   required, it should be required *after* the dismissals land, and the ruleset should
   probably be `error`-severity-only — noting that the single exploitable finding here was
   a `warning`, so severity alone is not a good filter either.

### What the spike did not get to

- The private-repo **existence oracle** via `POST /api/repos/subscribe` (a write-tier
  caller learns whether any private repo exists, using the operator's stored token). Noted
  under #51, deliberately excluded from Theme B's scope; it needs a design decision, not a
  message change. No CodeQL alert covers it.
- Whether the **read tier can reach any other unbounded regex**. I checked only
  `sanitize_fts_query` because that is what CodeQL flagged. `clipper.py`'s `_strip_elements`
  runs `re.sub` with `.*?` and `re.DOTALL` over attacker-influenced HTML on the write tier,
  which is the same rule's shape and was *not* flagged. Worth a follow-up spike rather than
  folding into Theme A.
- The `tests/e2e/conftest.py` suite writes into `~/.pyrite/repos/` (there are ~2400 stale
  `ephemeral/` dirs there). Unrelated test-hygiene issue, no alert, not chased.

## Groom 2026-09-18 (serial)

Re-cut after #168 (one Pyrite task at a time; each theme one worker pass and one review). Theme B is done (PR #161, awaiting review) and the eight `actions/missing-workflow-permissions` alerts landed in 28fc380. What remains, in order; the acceptance criteria under "2. Themes" above stand verbatim and are not repeated — this section adds the fields they lacked.

### A — `fix/search-query-length-cap` (the ReDoS; the one exploitable finding)

**Acceptance:** Theme A's seven criteria above, verbatim. One correction: criterion 3's "MCP `search` tool" is `kb_search` (`pyrite/server/tool_schemas.py:13`).
**Regimes:** a query of exactly 512, 513 and 100,000 characters; an empty and a whitespace-only query (today's behaviour unchanged); a 600-character query over **MCP**, where there is no 422 — say what the caller gets (truncate-and-search with a `warnings` entry, or a `VALIDATION_FAILED`; pick one, and it must not be a silent truncation that returns confident results for a query the caller did not send); multi-byte input (the cap counts characters, and a 512-character CJK query must not be cut mid-codepoint or exceed a byte limit downstream); the operator short-circuit path (`AND`/`OR`/quotes) with an over-long input — it returns before the `re.sub`, so prove the cap is applied before the short-circuit, not after; both call sites (`search_service.py` ~:270 and ~:388 — re-locate after #145) reached from REST, MCP and the CLI.
**Touches** — existing: `pyrite/services/search_service.py`, `pyrite/server/endpoints/search.py`, `pyrite/server/tool_schemas.py`, `CHANGELOG.md`. New: `tests/test_search_query_length_cap.py`.
**Sequence:** after PR #145 merges — hard conflict on all three existing files. Then first: it is the only remotely exploitable finding, on the read tier, and the alert page is public.
**Model:** opus. **heavy:** no. **Cold read:** yes. **Size:** S, ~120 lines (≈15 production).
**Out of scope:** rewriting the regex (criterion 7 — a reviewer seeing a regex change rejects the branch); a general request-size limit; rate limiting.

### C1 — `fix/github-token-host-equality` (the code half of Theme C)

**Acceptance:** Theme C's criteria 1 and 2, verbatim, plus the comment at `mcp_routes.py:182`. The PR body lists the alert numbers it makes dismissible (criterion 3).
**Regimes:** `https://github.com.evil.tld/a/b`, `https://evil.tld/github.com/a/b`, `https://user@github.com/a/b`, `git@github.com:a/b` (rewritten at `github_auth.py:355` before the check — still gets the token), `http://` (say whether a token is ever injected over plain HTTP), an empty/None URL, a GitHub Enterprise host (not supported today — must not get the github.com token).
**Touches** — existing: `pyrite/github_auth.py` (:363), `pyrite/services/user_service.py` (:83, comment), `pyrite/config.py` (:155 `is_github`, comment), `pyrite/server/mcp_routes.py` (:182, comment), `CHANGELOG.md`. New: a test beside the existing `github_auth` tests. `GitService._github_repo_path` (`git_service.py:434`) is **called, not edited**.
**Sequence:** after A and after #161 (Theme B) have merged — so both true positives are fixed before anything is dismissed — and #161 owns `git_service.py` until then.
**Model:** opus (auth; a token goes where this check says). **heavy:** no. **Cold read:** yes. **Size:** S, ~80 lines.
**Out of scope:** the dismissals (C2); making `config.py`/`user_service.py` use host equality (lookup-only uses — comments, per criterion 2).

### C2 — the 43 dismissals (not a worker theme, not a PR)

API calls the conductor makes from the dismissal table in section 3, each with the recorded reason, **after C1 merges and the next CodeQL run on `dev` has finished** (so alerts C1 fixed close themselves and are not dismissed by hand). Takes no machine slot. Afterwards: the open count on `dev` is the one maintainer-decision alert, and this item closes once D is decided.

### D — `docs/api-key-entropy` + `pyrite key new` — BLOCKED on the maintainer

Unchanged from Theme D above: dispatchable only if the maintainer's decision on `py/weak-sensitive-data-hashing` is "dismiss: sha256 of a high-entropy random key is sound". If the decision is "keyed hash", this theme is replaced (a breaking `config.yaml` change, its own ADR). **Regimes when it unblocks:** `--role` absent/invalid; stdout not a TTY (the key is still printed once, nothing is logged); two successive invocations differ. **Model:** sonnet. **heavy:** no. **Cold read:** yes (auth-adjacent CLI surface). **Size:** S, ~150 lines.

## Groom 2026-09-20

Spike re-run on `spike/codeql-triage`, **read-only** (no suite, no server — three code
workers held the machine). Evidence is `gh api` against the live alert set plus reading
`origin/dev` at `fbcd7b8`, with two throwaway `python3 -c` probes (regex timing, path
containment). **The inventory in the two sections above is stale and is superseded here.**

### 0. What changed since 2026-09-18, and why the count moved 56 → 47

Nine alerts left the open set. None of them was dismissed; all nine went to `fixed` because
code landed:

- The **8 `actions/missing-workflow-permissions`** alerts (#1–#8) closed with `28fc380`.
- **#35 `py/incomplete-url-substring-sanitization` `github_auth.py:363` is `fixed`.**
  Verified: `gh api .../alerts/35` returns `"state": "fixed"`, and
  `grep -n "github.com" pyrite/github_auth.py` now finds only the three module constants
  (`GITHUB_AUTHORIZE_URL`, `GITHUB_TOKEN_URL`, `GITHUB_API_URL`). The
  `if "github.com" in repo_url:` token-injection check no longer exists.
  **This voids Theme C1 entirely** — its acceptance criterion 1 is about a line that is
  gone. Do not dispatch C1 as written.
- **#41 `py/command-line-injection` `git_service.py:102` is `fixed`**; the surviving
  critical at that file is the renumbered **#57 at :212**. PR #161 rewrote `clone` into
  `clone_with_code` and moved everything down ~110 lines.

Two alerts are **code-fixed but still open**, which matters for sequencing: **#51/#52/#53**
(`repos.py`) were the subject of Theme B, and **PR #161 merged 2026-09-20T03:02Z**
implementing it in full — `_error_detail` → `_sanitized_message` → `GitService.sanitize_error`
→ `redact_paths(_sanitize_output(...))`, plus `classify_git_error` preserving the three
distinct codes. They should go to `fixed` on the next CodeQL run on `dev`. **Do not dismiss
them and do not re-dispatch Theme B.** If they are still open after the next scan, that is a
CodeQL taint-model limitation, not a missing fix, and *then* they become `false positive`
dismissals citing #161.

**PR #145 also merged (02:39Z), so `search_service.py` is clear.** Theme A's sequencing
blocker is gone and it is dispatchable now.

### 0b. Live inventory (47 open, 2026-09-20)

```
critical  py/command-line-injection                  #57    pyrite/services/git_service.py:212
critical  py/command-line-injection                  #42    pyrite/services/git_service.py:659
critical  py/full-ssrf                               #33    pyrite/services/clipper.py:188
high      py/clear-text-logging-sensitive-data       #10    pyrite/server/mcp_routes.py:182
high      py/clear-text-storage-sensitive-data       #9     scripts/scrape_appointee_details.py:627
high      py/incomplete-url-substring-sanitization   #34    pyrite/config.py:155
high      py/incomplete-url-substring-sanitization   #40    pyrite/services/user_service.py:83
high      py/incomplete-url-substring-sanitization   #36    tests/test_git_service.py:50
high      py/incomplete-url-substring-sanitization   #37    tests/test_llm_service.py:186
high      py/incomplete-url-substring-sanitization   #38    tests/test_llm_service.py:191
high      py/incomplete-url-substring-sanitization   #39    tests/test_notebooklm_renderer.py:254
high      py/path-injection                          #11    pyrite/server/branding_endpoints.py:61
high      py/path-injection                          #12    pyrite/services/branding_service.py:132
high      py/path-injection                          #13    pyrite/services/branding_service.py:139
high      py/path-injection                          #14    pyrite/services/export_service.py:64
high      py/path-injection                          #15    pyrite/services/export_service.py:69
high      py/path-injection                          #16    pyrite/services/export_service.py:83
high      py/path-injection                          #17    pyrite/services/export_service.py:112
high      py/path-injection                          #18    pyrite/services/export_service.py:161
high      py/path-injection                          #19    pyrite/services/kb_registry_service.py:118
high      py/path-injection                          #20    pyrite/server/static.py:132
high      py/path-injection                          #21    pyrite/server/static.py:138
high      py/path-injection                          #22    pyrite/server/static.py:139
high      py/path-injection                          #23    pyrite/server/static.py:239
high      py/path-injection                          #24    pyrite/server/static.py:245
high      py/path-injection                          #25    pyrite/server/static.py:247
high      py/polynomial-redos                        #43    pyrite/services/search_service.py:98
high      py/weak-sensitive-data-hashing             #26    pyrite/server/api.py:392
high      py/weak-sensitive-data-hashing             #27    pyrite/server/api.py:400
high      py/weak-sensitive-data-hashing             #28    pyrite/server/api.py:401
high      py/weak-sensitive-data-hashing             #29    tests/e2e/conftest.py:253
high      py/weak-sensitive-data-hashing             #30    pyrite/server/mcp_routes.py:67
high      py/weak-sensitive-data-hashing             #31    pyrite/server/mcp_routes.py:110
high      py/weak-sensitive-data-hashing             #32    pyrite/server/mcp_routes.py:118
medium    py/stack-trace-exposure                    #44    pyrite/server/endpoints/admin.py:136
medium    py/stack-trace-exposure                    #45    pyrite/server/endpoints/ai_ep.py:414
medium    py/stack-trace-exposure                    #46    pyrite/server/endpoints/entries.py:643
medium    py/stack-trace-exposure                    #47    pyrite/server/endpoints/git_ops.py:51
medium    py/stack-trace-exposure                    #48    pyrite/server/endpoints/git_ops.py:73
medium    py/stack-trace-exposure                    #49    pyrite/server/endpoints/git_ops.py:94
medium    py/stack-trace-exposure                    #50    pyrite/server/endpoints/kbs.py:182
medium    py/stack-trace-exposure                    #51    pyrite/server/endpoints/repos.py:160
medium    py/stack-trace-exposure                    #52    pyrite/server/endpoints/repos.py:184
medium    py/stack-trace-exposure                    #53    pyrite/server/endpoints/repos.py:303
medium    py/stack-trace-exposure                    #54    pyrite/server/endpoints/worktree.py:176
medium    py/stack-trace-exposure                    #55    pyrite/server/endpoints/worktree.py:184
medium    py/stack-trace-exposure                    #56    pyrite/server/endpoints/worktree.py:303
```

Rebuild with:
`gh api repos/markramm/pyrite/code-scanning/alerts --paginate --jq '.[] | select(.state=="open") | "\(.number)\t\(.rule.security_severity_level)\t\(.rule.id)\t\(.most_recent_instance.location.path):\(.most_recent_instance.location.start_line)"'`

### 0c. Summary

| Rule group | Count | Verdict |
|---|---|---|
| `py/command-line-injection` | 2 | noise (2) |
| `py/full-ssrf` | 1 | **hold** — noise as written, but #219 is open on the same line |
| `py/path-injection` | 15 | **mixed** — 1 true positive (#16), 14 noise |
| `py/stack-trace-exposure` | 13 | 3 already fixed by #161 (await rescan), 10 noise |
| `py/weak-sensitive-data-hashing` | 7 | 6 maintainer decision, 1 `used in tests` |
| `py/incomplete-url-substring-sanitization` | 6 | noise (2 code, 4 tests) |
| `py/polynomial-redos` | 1 | **true positive** (unchanged, still unfixed) |
| `py/clear-text-logging-sensitive-data` | 1 | noise |
| `py/clear-text-storage-sensitive-data` | 1 | noise |

**Two true positives need code: #43 (ReDoS, read tier) and #16 (`export_service.py:83`,
new this spike). 33 are dismissible immediately. 3 await a rescan. 6 await the maintainer.**

---

### 1. Verdicts on the three criticals

#### #57 `py/command-line-injection` `git_service.py:212` — **NOISE. The conductor's reading is correct, and I can add a fourth guard.**

The conductor named three guards; all four hold at the new line numbers:

1. **No `shell=True` anywhere in the package.** `grep -rn "shell=True" pyrite/` returns
   **zero lines**. This is stronger than "not in this file" — there is no shell in Pyrite.
2. **Leading-`-` rejection, at `git_service.py:198-203`**, with the comment naming the exact
   attack the conductor quoted:
   ```python
   # A value beginning with "-" would be parsed by git as an option
   # (--upload-pack=<cmd> is code execution). "--" below covers the
   # positionals; --branch's value is an option argument, so refuse it.
   if remote_url.startswith("-") or branch.startswith("-"):
       return False, "INVALID_REQUEST", "Invalid repository URL or branch"
   ```
   Note the comment's precision: `--` does *not* protect `--branch`'s value, which is why
   `branch` is checked separately. That is the subtle case, and it is handled.
3. **List argv with `--` before positionals** (`cmd.extend(["--", url, str(local_path)])`),
   `shell=False` by default, `env=_git_env()`.
4. **(Addition) `parse_github_url` upstream.** `RepoService.subscribe` does not hand
   arbitrary strings to `clone_with_code`; the URL first passes host-equality and
   `_GITHUB_NAME_RE.fullmatch` on owner and repo.

**Verdict: `false positive`.** No correction to the conductor.

#### #42 `py/command-line-injection` `git_service.py:659` — **NOISE, but the conductor's reasoning is incomplete — and the alert is not on the line the conductor triaged.**

The conductor's argument — "`git commit -m message`; `-m` consumes the next argv entry as a
value" — is right about `-m` and is *one* of the four flows CodeQL reports here. But the
API returns **four** `message.text` entries for #42 (`"This command line depends on a
user-provided value."` ×4), and `commit` runs **three** separate `subprocess.run` calls in
that block, not one:

- `git add -- <paths>` (~:635) — caller-supplied `paths` list. Protected by `--` + list argv.
- `git diff --cached --name-only` (:646) — no caller input at all.
- `git commit -m <message>` (:659) — the conductor's case. Correct.

The one the conductor did not name is **`paths`**, and it is the more interesting of the two:
it is a caller-supplied *list*, so `--` is doing the real work there, not `-m`'s
argument-consuming behaviour. `cwd=str(local_path)` is also service-derived, not caller-derived.

**Verdict is still `false positive`** — every flow is closed by list argv plus `--`, with no
shell — but the dismissal comment should say `--` and list argv, not `-m`, so it covers all
three subprocess calls. Written that way in the table below.

#### #33 `py/full-ssrf` `clipper.py:188` — **the conductor is right, and I would go further: do not dismiss this at all while #219 is open.**

Confirmed both halves:

- `_check_url_safe(url)` at `clipper.py:181` runs **before** any HTTP call. It rejects
  non-http(s) schemes, hostless URLs, IP literals in loopback/link-local/private/reserved/
  unspecified/multicast, and — after `getaddrinfo` — rejects if **any** resolved address is
  blocked (`for info in infos: ... _reject_if_blocked(ip, host)`), which closes the
  mixed public/private A-record trick.
- `follow_redirects=True` is at `clipper.py:185`, three lines after the check, and nothing
  revalidates a later hop. The docstring at :30-32 claims only DNS rebinding is residual,
  which is now **wrong** — the redirect bypass is a plain, no-race bypass: a public host
  returns `302 Location: http://169.254.169.254/...` and httpx follows it with no further
  check. That is #219.

**Recommendation: leave #33 open, do not dismiss, and let it close as `fixed` when #219
lands.** Rationale: the CodeQL alert and #219 point at the *same line* (`clipper.py:188`,
`client.get(url)`), and the rule's own wording — *"The full URL of this request depends on a
user-provided value"* — is, after the redirect, literally true. Dismissing it as a false
positive and then fixing the same line in #219 would leave a `dismissed` record contradicting
the fix. This is a **correction to the prior groom's dismissal table**, which listed #33 as
`false positive`.

Also worth recording on #219 while someone is in that file: `_strip_elements`
(`clipper.py:150-156`) runs six `re.sub` passes with `.*?` under `re.DOTALL` over
attacker-supplied HTML. Same rule family as #43, not flagged by CodeQL, not chased here.

---

### 2. NEW TRUE POSITIVE — `py/path-injection` #16 `export_service.py:83`

The prior groom dismissed all 15 path-injection alerts as noise, grouping
`export_service.py:64,69,83,112,161` under "the tainted value is `kb_name`, and
`self.config.get_kb(kb_name)` is a dict lookup". **That is right for :64, :69, :112 and :161
and wrong for :83.** At :83 the tainted value is not `kb_name`.

```python
for entry in entries:
    entry_type = entry.get("entry_type", "note")     # export_service.py:76
    ...
    type_dir = target_dir / entry_type               # :82
    type_dir.mkdir(parents=True, exist_ok=True)      # :83  <- alert #16
```

**There is no sanitizer on `entry_type`.** Contrast :112, three lines of logic later, where
the sibling value *is* sanitized: `file_path = type_dir / f"{sanitize_filename(entry_id)}.md"`.
The author sanitized the entry id and not the type.

**The data path, each hop verified:**

1. `POST /api/entries` → `entries.py:765` passes `req.entry_type or "note"` to
   `KBService.create_entry`. It is a free `str` on the request model; no enum, no allowlist.
   (`entries.py:630` is the same for the bulk-import route.)
2. `KBService.create_entry` (`kb_service.py:310`) calls `_resolve_entry_type`, which at
   `kb_service.py:249-251` does:
   ```python
   core_cls = ENTRY_TYPE_REGISTRY.get(entry_type)
   if not core_cls:
       return entry_type          # unknown type returned VERBATIM
   ```
   So `"../../../../tmp/pwned"` is not in the registry and is returned unchanged.
3. `build_entry` (`models/factory.py:38-41`) resolves an unknown type to `GenericEntry`
   rather than raising — unknown types are a supported feature.
4. `storage/models.py:53` — `entry_type = Column(String, nullable=False)`. No constraint.
   The value persists.
5. `ExportService.export_kb_to_directory` reads it back and joins it into a path.

**Containment probe** (`python3 -c`, no suite):
```
'../../escaped'   -> /private/var/folders/.../escaped       contained: False
'/tmp/abs-escape' -> /private/tmp/abs-escape                contained: False
'note'            -> .../export/note                        contained: True
```
`Path.__truediv__` with an absolute right operand **discards the left operand entirely**, so
an `entry_type` of `/etc/pyrite` targets `/etc/pyrite` directly — no `../` needed.

**Exploit shape.** Tier: **write**, two calls.
`POST /api/entries {"entry_type": "../../../../../../tmp/pwned", ...}` (write tier), then
`POST /api/kbs/{kb}/export` (`kbs.py:151`, `requires_tier("write")`, `5/minute`). Yield:
`mkdir(parents=True, exist_ok=True)` at an attacker-chosen absolute path, then
`file_path.write_text(content)` at :113 writing **attacker-controlled `body`** into
`<that dir>/<sanitized entry_id>.md`. That is arbitrary directory creation plus arbitrary
file write with controlled content, as the server user, outside the export tree. The `.md`
suffix and `sanitize_filename` on the basename constrain the filename but not the directory,
so any location that treats `*.md` as input (a KB the operator later indexes, a docs tree, a
web root) is writable. The same `entry_type` also reaches the export via the MCP
`entry_create` tool (`tool_schemas.py:664`, WRITE_TOOLS).

Not remotely exploitable by a read-tier or anonymous caller, so it is a rung below #43 in
urgency — but it is a genuine write-primitive, and the *only* true positive in the
path-injection group.

The other four `export_service` alerts stay noise: `get_kb` (`config.py:415-420`) is
`self._kb_by_name.get(name)` then `self._db_kb_cache.get(name)`, returning `None` →
`KBNotFoundError`. A traversal string is not a key.

---

### 3. `py/weak-sensitive-data-hashing` ×7 — what each hash is actually for

All six product-code sites are the **same operation**: sha256 of a presented API key,
compared with `secrets.compare_digest` against a stored `key_hash`. None is a cache key or an
ETag; this is credential verification. Read individually:

| # | Site | What the hash is for |
|---|---|---|
| 26 | `api.py:392` | `hashlib.sha256(key.encode()).hexdigest()` — the presented key, compared against each `api_keys[].key_hash`. **Credential verification.** |
| 27 | `api.py:400` | Same digest, legacy single-`api_key` branch — the presented key. **Credential verification.** |
| 28 | `api.py:401` | `sha256(config.settings.api_key.encode())` — the *configured* key, hashed at compare time so the plaintext is not held for comparison. **Credential verification**, the stored side. |
| 30 | `mcp_routes.py:67` | `hashlib.sha256(api_key.encode()).hexdigest()[:8]` → `f"apikey-{key_id}"` as a **log/display identifier**. **NOT a credential check** — a truncated fingerprint so the operator can tell two keys apart in logs without either appearing. |
| 31 | `mcp_routes.py:110` | `_resolve_api_key_role` — presented key. **Credential verification**, the MCP mirror of #26. |
| 32 | `mcp_routes.py:118` | Configured key, legacy branch. **Credential verification**, mirror of #28. |
| 29 | `tests/e2e/conftest.py:253` | Fixture minting `key_hash` for a throwaway read key. **Test data.** |

**#30 should be split out of the group.** It is the one alert here that is not auth at all —
it is an 8-hex-character display fingerprint, and sha256's cryptographic strength is
irrelevant to it. It is a clean `false positive` regardless of how the maintainer decides the
other five. The prior groom lumped it in with "same as #26, on the MCP auth path", which is
not what line 67 does.

**#26/#27/#28/#31/#32 — the decision stands, unchanged, and the premise still holds.** Two
things I re-verified rather than inherited:

- `grep -rn "token_urlsafe" pyrite/cli/` → **no hits**. There is still no `pyrite key new`.
  The only `token_urlsafe` uses are in `auth_service.py` (:35, :128, :579) for OAuth codes,
  state and session tokens — the session path does it right, the API-key path still leaves
  key choice to the human.
- `grep -rn "key_hash" docs/*.md` → **one line**, `docs/configuration.md:33`:
  `- key_hash: "<sha256 of the key>"`. Nothing tells the operator the key must be random.

So the gap the prior groom identified is real and unclosed: sha256 of a *random 32-byte* key
is sound and `compare_digest` closes timing, but nothing in Pyrite makes the key random.
**Recommendation unchanged: dismiss the five as `won't fix`, dismiss #30 as `false positive`,
dismiss #29 as `used in tests`, and dispatch Theme D.** Still the maintainer's call.

---

### 4. Remaining groups — corrections and confirmations

**`py/stack-trace-exposure` ×13.** #51/#52/#53 are **fixed in code by #161** (see §0) —
neither dismiss nor re-dispatch; await the rescan. The other ten are noise, and I re-verified
the two the prior groom reasoned about from line numbers that have since moved:

- #44 `admin.py:136` — the route is now annotated `# write tier: pings the provider with the
  operator's key`, `dependencies=[Depends(requires_tier("write"))]`, `10/minute`. Returns
  `llm.test_connection()`. Reporting why the operator's own provider call failed **is** the
  endpoint. `won't fix`.
- #45 `ai_ep.py:414` (was :376) — `str(e)` into an SSE `{"type":"error"}` frame with
  `logger.exception("AI chat stream error")` beside it. Same argument. `won't fix`.
- #46 `entries.py:643` (was :597) — `errors.append({"title": ..., "error": str(e)})` per row
  in a bulk import; the error describes the caller's own submitted row. `won't fix`.
- #47/#48/#49 `git_ops.py:51,73,94` (was :39,:61,:82) — each wraps the service call in
  `try: ... except KBNotFoundError: raise HTTPException(404, detail={"code": "NOT_FOUND", ...})`,
  a curated message, not an exception chain. `false positive`.
- #50 `kbs.py:182`, #54/#55/#56 `worktree.py` — unchanged from the prior groom; confirmed the
  worktree values are `GitService.diff_branches` output (a diff the caller may read), not an
  exception. `false positive`.

**`py/path-injection` — 14 of 15 noise, verified at current lines.**
`static.py:130-136` (`_serve_static_dir`) and `:237-243` (`_serve_site_cached`) both do
`resolved = ...resolve()` then `if not resolved.is_relative_to(directory.resolve()): return
HTMLResponse(status_code=404)` inside `except (ValueError, OSError)`. `resolve()` follows
symlinks before the comparison, so a symlink escape is caught too. `branding_service.py:132-139`
uses `candidate.relative_to(base)` in a `try/except ValueError` that logs
`"Asset traversal attempt rejected"` and returns `None`; `branding_endpoints.py:57-58` 404s on
`None`. `kb_registry_service.py:118` is admin-gated and registering a KB at an operator-chosen
path is the feature. CodeQL models neither `is_relative_to` nor `relative_to` as a barrier.

**`py/incomplete-url-substring-sanitization` ×6** (not 7 — #35 is fixed). `config.py:155`
`is_github` gates whether `github_oauth` is *configurable* for an operator-written remote;
no credential decision. `user_service.py:83` `"noreply.github.com" in email` parses a login
that is then only used for `self.db.get_user(github_login=login)` — a forged value returns
`None`, no account created, no trust granted. Four test assertions. All noise.
**Theme C1 as written is void** (§0); the `config.py` / `user_service.py` / `mcp_routes.py`
comments it carried are worth keeping — see Theme C1′.

**`py/polynomial-redos` #43 — still a true positive, still unfixed.** `search_service.py:98`
is unchanged: `re.sub(r"(\S*[^\w\s]\S*)", r'"\1"', query)`, and
`grep -rn "MAX_FTS_QUERY_CHARS\|max_length" search_service.py endpoints/search.py
tool_schemas.py` returns **nothing** — the cap was never added. `endpoints/search.py:38` is
still `q: str = Query(..., min_length=1, ...)` with no `max_length`, behind
`dependencies=[Depends(requires_kb_read())]` (**read tier**). Re-measured on this machine:
```
n=  1000       4.4 ms
n=  5000     136.5 ms
n= 20000    2074.4 ms
n= 50000   14972.0 ms
capped 512:  1.370 ms
```
Quadratic (4x length → ~15x time, 2.5x → ~7x). 15 s of single-threaded CPU for one read-tier
request at 50k characters, against a `100/minute` limit. Theme A stands verbatim and is now
**unblocked** (#145 merged).

**#10 `clear-text-logging` `mcp_routes.py:182`** — confirmed at the current line:
`logger.info("MCP SSE connection: user=%s tier=%s", client_id, tier)`, where `tier` is one of
the three literals (`:180` — `tier = role if role in ("read","write","admin") else "read"`)
and `client_id` is `f"apikey-{sha256(key)[:8]}"`. The key never reaches the log. `false positive`.

**#9 `clear-text-storage` `scripts/scrape_appointee_details.py:627`** — `person_path.write_text(new_text)`
in a one-off scraper for published ProPublica disclosures. Not in the package, not on a
request path. `won't fix`.

---

### 5. Themes, in dispatch order

Cold read **yes** for every theme (security-adjacent by definition). **Never `good first
issue`.** `heavy: no` throughout.

**Collision check against work in flight.** Actively edited right now: `server/api.py`,
`server/mcp_routes.py`, `server/mcp_server.py` (#201); `services/kb_service.py`,
`services/embedding_worker.py`, `server/endpoints/admin.py`, `cli/index_commands.py` (#13);
`server/endpoints/repos.py` (#195). Of the files these themes touch:
- **A** (`search_service.py`, `endpoints/search.py`, `tool_schemas.py`) — **no collision.**
  #145 merged; #201 is in `mcp_server.py`/`mcp_routes.py`, not `tool_schemas.py`. Confirm
  `tool_schemas.py` is untouched at dispatch, since #201 is MCP-adjacent.
- **E** (`export_service.py` + a validator) — **collides with #13 if the validator lands in
  `kb_service.py`.** Acceptance criterion 1 below puts it in `pyrite/utils/sanitize.py`
  instead, which nobody holds, and criterion 2 keeps the `kb_service.py` edit to a single
  call site. Still: **sequence E after #13 merges**, or accept a one-line rebase.
- **C1′** (`config.py`, `user_service.py`, `mcp_routes.py`) — **collides with #201 on
  `mcp_routes.py`.** Sequence after #201.
- **D** — blocked on the maintainer; touches `docs/` and `cli/` (a new file, not
  `index_commands.py`).

#### A — `fix/search-query-length-cap` — the ReDoS. **Dispatch first.**

**Unblocked as of 2026-09-20T02:39Z (#145 merged).** Acceptance criteria, regimes, touches,
out-of-scope: exactly as in `## Groom 2026-09-18 (serial)` §A above, verbatim, including
criterion 7 (**do not rewrite the regex** — the `(?=\S*[^\w\s])(\S+)` rewrite is byte-identical
in output, still quadratic, and 7.3x slower at n=100000; a reviewer seeing a regex change
rejects the branch). The measurement in §4 above replaces the older numbers.
**Model:** opus. **Cold read:** yes. **Size:** S, ~120 lines (≈15 production).
**Collides with:** nothing. **Closes:** #43.

#### E — `fix/export-entry-type-path-injection` — the new true positive. **Dispatch second.**

**Model: opus** (it adds a validator on a write-tier path and must not break the
unknown-entry-type feature, which is deliberate — see `_resolve_entry_type`'s docstring and
`GenericEntry`). **Sequence: after #13 merges** (`kb_service.py`), or accept a one-line rebase.
**Cold read:** yes. **heavy:** no. **Size:** S, ~130 lines (≈25 production).

Touches (existing): `pyrite/utils/sanitize.py`, `pyrite/services/export_service.py`,
`pyrite/services/kb_service.py` (**one call site only**), `CHANGELOG.md`.
Touches (new): `tests/test_export_entry_type_path.py`.

Acceptance criteria:
1. A new `sanitize_type_dir(entry_type: str) -> str` in `pyrite/utils/sanitize.py` (**not**
   in `kb_service.py` — that file is held by #13) reduces any entry type to a single safe
   path segment: no `/`, no `\`, no `..`, never absolute, never empty (fall back to
   `"note"`). A test table asserts at minimum
   `"../../escaped"`, `"/tmp/abs-escape"`, `"..%2f.."`, `""`, `"."`, `".."`, `"a/b"`,
   `"C:\\x"` each produce a segment for which
   `(target / result).resolve().is_relative_to(target.resolve())` is **True**.
2. `export_service.py:82` uses it: `type_dir = target_dir / sanitize_type_dir(entry_type)`.
   A test exports a KB containing an entry whose stored `entry_type` is
   `"../../../../tmp/pyrite-escape-test"` and asserts (a) nothing is created outside
   `target_dir`, and (b) the entry is still exported, under a contained directory.
   **The export must not fail** — a malformed type is not a reason to lose an entry.
3. **Defence in depth at the source:** `KBService.create_entry` rejects an `entry_type` that
   is not a single safe segment, with `ValidationError`, *before* it is persisted. It must
   **not** reject unknown-but-safe types — `_resolve_entry_type` deliberately returns unknown
   types verbatim and `build_entry` falls back to `GenericEntry`; a test asserts
   `entry_type="my_custom_type"` still round-trips and still lands in `GenericEntry`.
   This is one call site in `kb_service.py`; keep the diff there to that.
4. A test asserts the bulk-import path (`entries.py:630`) and the MCP `entry_create` tool
   reach the same validation, not just `POST /api/entries`.
5. `sanitize_filename`'s behaviour is unchanged — this is a new function beside it, not an
   edit to it. Existing `tests/` for `sanitize_filename` pass untouched.
6. A migration note in `CHANGELOG.md`: KBs that already contain an entry with a path-bearing
   `entry_type` export into a contained directory from now on; no data is rewritten.

Out of scope, name in the PR body and do not chase: retro-actively cleaning existing rows;
`export_service.py:161`'s `clone_path` (registry-gated, noise); an allowlist of entry types
(would break the plugin-type feature).

**Closes:** #16. **Does not** close #14/#15/#17/#18 — those are separate dismissals.

#### B — **DONE. Do not dispatch.** PR #161 merged 2026-09-20T03:02Z.

`_error_detail` / `_sanitized_message` / `GitService.sanitize_error` / `redact_paths` /
`classify_git_error` are all in place at `origin/dev`. #51/#52/#53 should auto-close on the
next CodeQL run. The private-repo existence oracle remains deliberately out of scope
(needs a design decision; no alert covers it).

#### C1′ — `chore/security-comments-on-noise-sites` — optional, low value

**Theme C1 as written is void**: its criterion 1 targets `"github.com" in repo_url` in
`github_auth.py`, which no longer exists (#35 is `fixed`). What survives is comments only:
at `config.py:155` (`is_github` gates a config warning, not a credential), `user_service.py:83`
(the parsed login is lookup-only), `mcp_routes.py:182` (only the tier literal and a truncated
hash are logged — so the next reader does not "fix" it by deleting the log).
**No behaviour change, no test change.** **Model:** sonnet (comments only, nothing changes a
check — this is the one theme here that does not need opus, precisely because it changes
nothing). **Cold read:** yes. **Sequence: after #201 merges** (`mcp_routes.py`). **Size:** XS.
Fold into any docs pass rather than dispatching on its own.

#### D — `docs/api-key-entropy` + `pyrite key new` — **BLOCKED on the maintainer**

Unchanged from `## Groom 2026-09-18 (serial)` §D. Re-verified this spike that the gap is
still open: no `token_urlsafe` in `pyrite/cli/`, and `docs/configuration.md:33` is the only
mention of `key_hash`. **Model:** sonnet. **Cold read:** yes. **Size:** S, ~150 lines.
Touches `docs/configuration.md` + a new CLI module + `CHANGELOG.md` — **no collision** with
#13's `cli/index_commands.py`.

---

### 6. Dismissal table — 33 dismissible immediately

```
gh api -X PATCH repos/markramm/pyrite/code-scanning/alerts/<n> \
  -f state=dismissed -f dismissed_reason='<reason>' -f dismissed_comment='<one line>'
```

These 33 depend on no theme and can be dismissed **now** — they are noise regardless of what
lands. (The prior groom's table said "dismiss after A and B merge"; that constraint applied to
alerts a fix would close. None of these is one.)

| # | Rule | Reason | Comment |
|---|---|---|---|
| 9 | clear-text-storage | `won't fix` | One-off scraper for published ProPublica disclosures; CodeQL matched the local name `private`. Not in the package, not on a request path. |
| 10 | clear-text-logging | `false positive` | The flagged value is `tier`, one of the literals read/write/admin (mcp_routes.py:180); `client_id` is a truncated sha256 fingerprint. The key never reaches the log. |
| 11 | path-injection | `false positive` | `branding_endpoints` 404s when `resolve_asset` returns None; `resolve_asset` enforces `candidate.relative_to(branding_dir)` and logs rejected traversals. |
| 12 | path-injection | `false positive` | `branding_service.resolve_asset` enforces `relative_to(base)` after `resolve()`, so symlink escapes are caught too. CodeQL does not model `relative_to` as a barrier. |
| 13 | path-injection | `false positive` | Same `relative_to` containment guard in `resolve_asset`. |
| 14 | path-injection | `false positive` | `kb_name` is a dict-lookup key into the registered-KB map (`config.get_kb` → `_kb_by_name.get` / `_db_kb_cache.get`); an unregistered value raises KBNotFoundError before any path use. |
| 15 | path-injection | `false positive` | Same registry-lookup barrier on `kb_name`. |
| 17 | path-injection | `false positive` | The entry filename goes through `sanitize_filename` (utils/sanitize.py), which strips separators and `..` and takes the basename. |
| 18 | path-injection | `false positive` | `clone_path` is derived from the registry-validated `kb_name`, not from caller input. |
| 19 | path-injection | `won't fix` | Registering a KB at an operator-chosen path is the feature; the only route, `POST /api/kbs`, is admin tier. No privilege boundary is crossed. |
| 20 | path-injection | `false positive` | `_serve_static_dir` enforces `resolved.is_relative_to(directory.resolve())` and 404s otherwise, inside try/except (ValueError, OSError). `resolve()` runs before the comparison, so symlink escapes are caught. |
| 21 | path-injection | `false positive` | Same containment guard in `_serve_static_dir`. |
| 22 | path-injection | `false positive` | Same containment guard in `_serve_static_dir`. |
| 23 | path-injection | `false positive` | `_serve_site_cached` enforces the same `is_relative_to` containment before reading. |
| 24 | path-injection | `false positive` | Same containment guard in `_serve_site_cached`. |
| 25 | path-injection | `false positive` | Same containment guard in `_serve_site_cached`. |
| 29 | weak-hashing | `used in tests` | e2e fixture minting a throwaway read key's `key_hash`. |
| 30 | weak-hashing | `false positive` | Not a credential check: `sha256(api_key)[:8]` is an 8-hex display fingerprint for the log identifier `apikey-<id>`, so two keys are distinguishable in logs without either appearing. Hash strength is irrelevant here. |
| 34 | incomplete-url-sanitization | `false positive` | `RepoConfig.is_github` gates whether the `github_oauth` method is configurable for an operator-written remote in config.yaml; no credential decision depends on it. |
| 36 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 37 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 38 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 39 | incomplete-url-sanitization | `used in tests` | Test assertion on a URL string. |
| 40 | incomplete-url-sanitization | `false positive` | The login parsed from a noreply address is only used for `db.get_user(github_login=...)`; a forged value returns None. No account is created and no trust is granted. |
| 42 | command-line-injection | `false positive` | All three subprocess calls in `commit` use list argv with no shell: `git add --` separates the caller's paths from options, and `git commit -m <msg>` passes the message as an option argument. `shell=True` appears nowhere in the package. |
| 44 | stack-trace-exposure | `won't fix` | `llm.test_connection()`'s diagnostic is the endpoint's entire purpose (write tier, operator's own provider); suppressing it removes the feature. |
| 45 | stack-trace-exposure | `won't fix` | `str(e)` in an SSE error frame on the operator's own LLM stream, with `logger.exception` beside it. Same argument as #44. |
| 46 | stack-trace-exposure | `won't fix` | Per-row bulk-import error describing the caller's own submitted row. |
| 47 | stack-trace-exposure | `false positive` | Admin-gated; the body is a curated `{"code","message"}` PyriteError dict, not an exception chain. |
| 48 | stack-trace-exposure | `false positive` | Same: admin tier, curated COMMIT_FAILED/NOT_FOUND message. |
| 49 | stack-trace-exposure | `false positive` | Same: admin tier, curated PUSH_FAILED/NOT_FOUND message. |
| 54 | stack-trace-exposure | `false positive` | Requires `request.state.auth_user`; the value is `GitService.diff_branches` output — a git diff the caller is authorised to read — not an exception. |
| 55 | stack-trace-exposure | `false positive` | Same: authenticated worktree diff content. |
| 56 | stack-trace-exposure | `false positive` | Same: authenticated worktree diff content. |

**#57** is `false positive` too, and can go with the 33, with this comment: *"Four guards:
`shell=True` appears nowhere in the package; `clone_with_code` refuses a leading `-` on both
`remote_url` and `branch` (--upload-pack=<cmd>); the argv is a list with `--` before the
positionals; and `parse_github_url` enforces https + host equality + `_GITHUB_NAME_RE.fullmatch`
upstream."* Listed separately only because it is the one critical the conductor triaged by hand.

**Do NOT dismiss, with reasons:**

| # | Why not |
|---|---|
| 16 | **True positive.** Fixed by Theme E; must close as `fixed`. |
| 33 | **Hold.** #219 (redirect SSRF bypass) is open on the same line; a `dismissed` record would contradict the fix. Let #219 close it. |
| 43 | **True positive.** Fixed by Theme A; must close as `fixed`. |
| 51, 52, 53 | **Already fixed in code** by #161. Await the next CodeQL run on `dev`. Only if they are still open after that rescan do they become `false positive` dismissals citing #161's `sanitize_error`/`redact_paths`. |
| 26, 27, 28, 31, 32 | **Maintainer decision** pending (§3). Recommendation: `won't fix`. |

**Arithmetic:** 47 open = 33 dismissible now + 1 (#57, also dismissible) + 2 true positives
(#16, #43) + 1 held (#33) + 3 awaiting rescan (#51-53) + 5 maintainer (#26,27,28,31,32)
+ 2 (#29 and #30 are inside the 33) → the projected open count after A, E, the rescan and the
dismissals is **5**, all of them the weak-hashing decision, and **0** once that is recorded.

### 7. What this spike could not determine

- **Whether #51/#52/#53 actually close on rescan.** I cannot trigger a CodeQL run from here
  and would not spend a machine slot on it. Resolving it costs one scan on `dev` after the
  next merge — check `gh api .../alerts/51 --jq .state` then.
- **Whether `entry_type` traversal survives a round-trip through the filesystem KB store**
  (not just the DB). I verified DB persistence (`storage/models.py:53`, no constraint) and the
  path join, but not what the markdown writer does with a path-bearing `type:` in frontmatter.
  It does not change Theme E's verdict — the export path is the write primitive either way —
  but a worker should check whether the *creation* path also escapes, which would raise the
  severity. Costs one `pytest -k` run or a direct call; needs a machine slot.
- **`clipper.py:150-156`'s six `.*?`/`re.DOTALL` substitutions over attacker HTML** — same
  rule family as #43, on the write tier, not flagged by CodeQL and not measured here. Worth a
  note on #219 rather than a theme of its own.
- **Whether CodeQL should become a required check** (the maintainer's kept decision on this
  item). New evidence for it: of 47 alerts, 2 are true positives, 1 is held for an open issue,
  and 44 are noise or decisions — a ~4% signal rate. Severity is not a usable filter either:
  both true positives are `high`, while all three `critical`s are noise. If it becomes
  required, require it only after the dismissals land.
