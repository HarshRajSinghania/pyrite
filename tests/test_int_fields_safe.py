"""Integer fields loaded from frontmatter go through safe_int and do not raise."""

import pytest
from pyrite.utils.yaml import load_yaml

from pyrite_social.entry_types import UserProfileEntry
from pyrite_software_kb.entry_types import ADREntry, BacklogItemEntry


@pytest.mark.parametrize("literal", [".inf", "-.inf", ".nan", "high", None])
def test_user_profile_int_fields_safe(literal):
    meta = load_yaml(f"id: u1
title: User
reputation: {literal}
writeup_count: {literal}
")
    entry = UserProfileEntry.from_frontmatter(meta, "body")
    assert entry.reputation == 0
    assert entry.writeup_count == 0
    assert entry.id == "u1"


@pytest.mark.parametrize("literal", [".inf", "-.inf", ".nan", "high"])
def test_adr_and_backlog_int_fields_safe(literal):
    adr_meta = load_yaml(f"id: a1
title: ADR
adr_number: {literal}
")
    adr = ADREntry.from_frontmatter(adr_meta, "")
    assert adr.adr_number == 0

    bl_meta = load_yaml(f"id: b1
title: Item
rank: {literal}
")
    bl = BacklogItemEntry.from_frontmatter(bl_meta, "")
    assert bl.rank == 0
