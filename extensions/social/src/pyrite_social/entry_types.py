"""Social KB entry types."""

from dataclasses import dataclass
from typing import Any

from pyrite.models.core_types import NoteEntry, PersonEntry
from pyrite.utils.parse import safe_int

WRITEUP_TYPES = ("essay", "story", "review", "howto", "opinion")


@dataclass
class WriteupEntry(NoteEntry):
    """A user-authored writeup in a social knowledge base.

    Stored in folder-per-author layout: writeups/<author_id>/slug.md
    """

    author_id: str = ""
    writeup_type: str = "essay"  # essay, story, review, howto, opinion
    allow_voting: bool = True


@dataclass
class UserProfileEntry(PersonEntry):
    """A user profile in a social knowledge base."""

    role: str = ""
    affiliations: list[str] = field(default_factory=list)
    research_status: ResearchStatus = ResearchStatus.STUB
    reputation: int = 0
    join_date: str = ""
    writeup_count: int = 0

    def from_frontmatter(cls, meta: dict[str, Any], body: str) -> "UserProfileEntry":
        from pyrite.schema import ResearchStatus

        status_str = meta.get("research_status", "stub")
        try:
            research_status = ResearchStatus(status_str)
        except ValueError:
            research_status = ResearchStatus.STUB

        kw = cls._base_kwargs(meta, body)
        kw["role"] = meta.get("role", "")
        kw["affiliations"] = meta.get("affiliations", []) or []
        kw["research_status"] = research_status
        kw["reputation"] = safe_int(meta.get("reputation", 0))
        kw["join_date"] = meta.get("join_date", "")
        kw["writeup_count"] = safe_int(meta.get("writeup_count", 0))
        return cls(**kw)
