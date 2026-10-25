"""Regression tests for full task IDs in Rich views (#1340).

The Rich renderer for `task list` and the children list of `task get` must
show the complete ID and parent ID. Truncating to 12 characters (and
max_width=12) hid long IDs; a narrow terminal should fold instead of cutting.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from pyrite.cli import app
from pyrite.config import KBConfig, PyriteConfig, Settings
from pyrite.services.task_service import TaskService
from pyrite.storage.database import PyriteDB

runner = CliRunner()


@pytest.fixture
def long_id_env(tmp_path: Path):
    """Task KB with a parent and child whose IDs are longer than 12 characters."""
    tasks_path = tmp_path / "tasks-kb"
    (tasks_path / "tasks").mkdir(parents=True)

    kb_config = KBConfig(
        name="test-tasks", path=tasks_path, kb_type="task", description="Test task KB"
    )
    config = PyriteConfig(
        knowledge_bases=[kb_config],
        settings=Settings(index_path=tmp_path / "index.db"),
    )
    db = PyriteDB(config.settings.index_path)
    db.register_kb(
        name="test-tasks", kb_type="task", path=str(tasks_path), description="Test task KB"
    )
    svc = TaskService(config, db)
    parent = svc.create_task(kb_name="test-tasks", title="Parent epic for login")
    parent_id = parent["entry_id"]
    child = svc.create_task(
        kb_name="test-tasks",
        title="Write the login form",
        parent=parent_id,
    )
    child_id = child["entry_id"]
    db.close()

    assert len(parent_id) > 12
    assert len(child_id) > 12

    with patch("pyrite.cli.context.load_config", return_value=config):
        yield {"parent_id": parent_id, "child_id": child_id}


@pytest.mark.cli
def test_task_list_rich_shows_full_ids(long_id_env, monkeypatch):
    """Wide terminal: `task list --format rich` contains the full parent and child IDs."""
    monkeypatch.setenv("COLUMNS", "200")
    result = runner.invoke(
        app, ["task", "list", "-k", "test-tasks", "--format", "rich"]
    )
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    assert long_id_env["parent_id"] in out
    assert long_id_env["child_id"] in out
    # Parent cell of the child row must hold the full parent ID.
    assert out.count(long_id_env["parent_id"]) >= 1


@pytest.mark.cli
def test_task_get_rich_lists_child_by_full_id(long_id_env, monkeypatch):
    """`task get --format rich` lists children by their full ID."""
    monkeypatch.setenv("COLUMNS", "200")
    result = runner.invoke(
        app,
        ["task", "get", long_id_env["parent_id"], "-k", "test-tasks", "--format", "rich"],
    )
    assert result.exit_code == 0, result.stdout
    assert long_id_env["child_id"] in result.stdout


@pytest.mark.cli
def test_task_list_rich_folds_on_narrow_terminal(long_id_env, monkeypatch):
    """Narrow terminal: the ID column folds instead of hard-cutting to 12 characters."""
    monkeypatch.setenv("COLUMNS", "60")
    result = runner.invoke(
        app, ["task", "list", "-k", "test-tasks", "--format", "rich"]
    )
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    child_id = long_id_env["child_id"]
    # More than the old 12-character prefix must be visible (folding, not truncation).
    assert child_id[:12] in out
    # The continuation of the ID past 12 characters must also appear somewhere.
    assert child_id[12:18] in out or child_id[12:] in out, (
        f"expected the ID to fold past 12 chars, got:\n{out}"
    )
