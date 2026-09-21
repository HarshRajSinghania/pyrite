"""A KB registered in the database is visible to the task commands (#245).

`kb create` and `kb add` register a KB in the database registry; every other
CLI path merges that registry into the config before use. The task commands
read the YAML config directly, so a registered KB answered KB_NOT_FOUND while
`kb list` still showed it — success and discoverability both lying about
write-readiness.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from pyrite.cli import app
from pyrite.config import PyriteConfig, Settings
from pyrite.storage.database import PyriteDB

runner = CliRunner()


def _env(tmp_path: Path) -> tuple[PyriteConfig, PyriteDB]:
    """A config that knows no KBs, plus a KB registered only in the database."""
    kb_path = tmp_path / "reg-kb"
    kb_path.mkdir()
    (kb_path / "kb.yaml").write_text("name: reg-kb\nkb_type: generic\n", encoding="utf-8")

    db_path = tmp_path / "index.db"
    config = PyriteConfig(knowledge_bases=[], settings=Settings(index_path=db_path))
    db = PyriteDB(db_path)
    db.register_kb(name="reg-kb", kb_type="generic", path=str(kb_path), description="")
    return config, db


def _invoke(config: PyriteConfig, args: list[str]):
    # The task path reads the config through the shared CLI loader; the module
    # attribute is patched too so the test is red before the fix and green after
    # it, whichever of the two the command reads.
    with (
        patch("pyrite.cli.context.load_config", return_value=config),
        patch("pyrite.cli.task_commands.load_config", return_value=config, create=True),
    ):
        return runner.invoke(app, args)


def test_task_create_sees_a_database_registered_kb(tmp_path):
    config, db = _env(tmp_path)
    try:
        result = _invoke(
            config, ["task", "create", "registered probe", "-k", "reg-kb", "--format", "json"]
        )

        assert result.exit_code == 0, result.output
    finally:
        db.close()


def test_task_list_sees_a_database_registered_kb(tmp_path):
    config, db = _env(tmp_path)
    try:
        created = _invoke(
            config, ["task", "create", "listed probe", "-k", "reg-kb", "--format", "json"]
        )
        assert created.exit_code == 0, created.output

        listed = _invoke(config, ["task", "list", "-k", "reg-kb", "--format", "json"])

        assert listed.exit_code == 0, listed.output
        assert "listed-probe" in listed.output
    finally:
        db.close()


def test_an_unknown_kb_still_reports_kb_not_found(tmp_path):
    config, db = _env(tmp_path)
    try:
        result = _invoke(config, ["task", "create", "nowhere", "-k", "nope", "--format", "json"])

        assert result.exit_code != 0
        assert "KB_NOT_FOUND" in result.output
    finally:
        db.close()
