"""Non-finite YAML numbers follow the same fallback as other invalid integers."""

from decimal import Decimal

import pytest

from pyrite.models import NoteEntry, TaskEntry
from pyrite.models.core_types import QAAssessmentEntry
from pyrite.utils.parse import safe_int
from pyrite.utils.yaml import load_yaml


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan"), Decimal("Infinity")])
def test_nonfinite_safe_int_uses_the_callers_default(value):
    assert safe_int(value, 17) == 17


@pytest.mark.parametrize("literal", [".inf", "-.inf", ".nan"])
def test_nonfinite_common_fields_do_not_abort_loading(literal):
    meta = load_yaml(
        f"id: note-1\ntitle: Retain me\nimportance: {literal}\n_schema_version: {literal}\n"
    )
    entry = NoteEntry.from_frontmatter(meta, "The body is still readable.")
    assert entry.id == "note-1"
    assert entry.importance == 5
    assert entry._schema_version == 0
    assert entry.body == "The body is still readable."
    assert str(meta["importance"]) in {"inf", "-inf", "nan"}  # source value was not repaired


@pytest.mark.parametrize("literal", [".inf", "-.inf"])
def test_assessment_fields_fall_back_and_task_keeps_its_own_priority_policy(literal):
    task = TaskEntry.from_frontmatter(load_yaml(f"id: t\ntitle: Task\npriority: {literal}\n"), "")
    assessment = QAAssessmentEntry.from_frontmatter(
        load_yaml(
            f"id: a\ntitle: Assessment\ntier: {literal}\n"
            f"issues_found: {literal}\nissues_resolved: {literal}\n"
        ),
        "",
    )
    assert task.priority == 5
    assert (assessment.tier, assessment.issues_found, assessment.issues_resolved) == (1, 0, 0)


@pytest.mark.parametrize(
    ("value", "expected"), [("12", 12), (3.8, 3), (-2, -2), (None, 9), ("bad", 9)]
)
def test_finite_and_previously_invalid_inputs_are_unchanged(value, expected):
    assert safe_int(value, 9) == expected


# Additional coverage for #1247: extension integer fields
@pytest.mark.parametrize("literal", [".inf", "-.inf", ".nan", "high"])
def test_social_profile_integer_fields_fall_back(literal):
    from pyrite_social.entry_types import UserProfileEntry

    meta = load_yaml(
        f"id: u1\ntitle: User\nreputation: {literal}\nwriteup_count: {literal}\n"
    )
    entry = UserProfileEntry.from_frontmatter(meta, "profile")
    assert entry.reputation == 0
    assert entry.writeup_count == 0
    assert entry.entry_type == "user_profile"


@pytest.mark.parametrize("literal", [".inf", "-.inf", ".nan"])
def test_software_kb_rank_and_adr_number_fall_back(literal):
    from pyrite_software_kb.entry_types import BacklogItemEntry, ADREntry

    bl = BacklogItemEntry.from_frontmatter(
        load_yaml(f"id: b1\ntitle: Item\nrank: {literal}\n"), ""
    )
    assert bl.rank == 0
    assert bl.entry_type == "backlog_item"

    adr = ADREntry.from_frontmatter(
        load_yaml(f"id: a1\ntitle: ADR\nadr_number: {literal}\n"), ""
    )
    assert adr.adr_number == 0
    assert adr.entry_type == "adr"
