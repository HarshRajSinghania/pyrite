"""One narrowing rule for KB-scoped reads in plugin tools (#223).

A plugin tool can declare its KB parameter *optional*, which means a call that
omits it spans every KB. `_dispatch_tool` will not serve such a call to a
scoped caller unless the handler can narrow itself -- it fails closed instead
(#201) -- so handing the handler the caller's readable set is what turns that
refusal back into a filtered answer.

The narrowing is the same whichever extension asks, and six of them do (#223),
so it lives here rather than once per plugin: the sixth copy is the one that
quietly forgets the empty case.
"""

from __future__ import annotations


def kb_scope_clause(
    column: str, kb_name: str | None, readable_kbs: set[str] | None
) -> tuple[str, list[str]]:
    """A SQL `AND ...` narrowing for one KB-bearing read, with its parameters.

    - A **named KB wins**: the chokepoint has already refused one the caller
      may not read, so binding it is both correct and narrower than the set.
    - **No name plus a readable set** narrows to that set. An *empty* set
      matches nothing (`AND 1 = 0`) rather than emitting `IN ()`, which is a
      syntax error, and rather than quietly spanning the index.
    - `readable_kbs=None` is the unscoped caller -- a global admin, an operator
      API key, local stdio -- and adds no narrowing at all, as before.
    """
    if kb_name:
        return f" AND {column} = ?", [kb_name]
    if readable_kbs is None:
        return "", []
    if not readable_kbs:
        return " AND 1 = 0", []
    placeholders = ",".join("?" for _ in readable_kbs)
    return f" AND {column} IN ({placeholders})", sorted(readable_kbs)
