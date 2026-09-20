"""`pyrite update -f` must parse values the way `create -f` does (#231).

`-f tags=alpha,beta` used to store the raw string ``alpha,beta`` because the
update path coerced ints only while the create path used the full value parser.
The reader then iterated the string as a sequence, so the entry came back tagged
with the characters of the value and silently dropped out of tag lookups.
"""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from pyrite.cli import app
from pyrite.config import KBConfig, KBType, PyriteConfig, Settings
from pyrite.storage.database import PyriteDB
from pyrite.utils.yaml import load_yaml

runner = CliRunner()

KB_YAML = """name: notes
kb_type: generic
types:
  note:
    description: A note
"""


def _make_env(tmp_path: Path) -> tuple[PyriteConfig, Path]:
    kb_path = tmp_path / "kb"
    kb_path.mkdir()
    (kb_path / "kb.yaml").write_text(KB_YAML, encoding="utf-8")
    db_path = tmp_path / "index.db"
    PyriteDB(db_path).close()
    kb = KBConfig(name="notes", path=kb_path, kb_type=KBType.GENERIC)
    config = PyriteConfig(knowledge_bases=[kb], settings=Settings(index_path=db_path))
    return config, kb_path


def _invoke(config: PyriteConfig, args: list[str]):
    with patch("pyrite.cli.context.load_config", return_value=config):
        return runner.invoke(app, args)


def _json_payload(result) -> dict:
    text = result.output.strip()
    return json.loads(text[text.index("{") :])


def _entry_id(kb_path: Path) -> str:
    files = list(kb_path.rglob("*.md"))
    assert len(files) == 1, files
    return files[0].stem


def _create_note(config: PyriteConfig) -> None:
    result = _invoke(
        config,
        ["create", "-k", "notes", "-t", "note", "--title", "Tag probe", "-b", "body"],
    )
    assert result.exit_code == 0, result.output


def test_update_field_writes_a_comma_separated_value_as_a_list(tmp_path):
    config, kb_path = _make_env(tmp_path)
    _create_note(config)
    entry_id = _entry_id(kb_path)

    result = _invoke(
        config, ["update", entry_id, "-k", "notes", "-f", "tags=alpha,beta", "--format", "json"]
    )
    assert result.exit_code == 0, result.output

    # The file must not carry the raw string: that is what got read back as the
    # characters a, l, p, h, ...
    text = list(kb_path.rglob("*.md"))[0].read_text(encoding="utf-8")
    assert "alpha,beta" not in text, text

    payload = _json_payload(_invoke(config, ["get", entry_id, "-k", "notes", "--format", "json"]))
    assert payload["tags"] == ["alpha", "beta"], payload


def test_update_field_matches_the_dedicated_tags_flag(tmp_path):
    config, kb_path = _make_env(tmp_path)
    _create_note(config)
    entry_id = _entry_id(kb_path)

    result = _invoke(
        config, ["update", entry_id, "-k", "notes", "--tags", "alpha,beta", "--format", "json"]
    )
    assert result.exit_code == 0, result.output

    payload = _json_payload(_invoke(config, ["get", entry_id, "-k", "notes", "--format", "json"]))
    assert payload["tags"] == ["alpha", "beta"], payload


def test_update_field_still_parses_scalars_and_json(tmp_path):
    config, kb_path = _make_env(tmp_path)
    _create_note(config)
    entry_id = _entry_id(kb_path)

    result = _invoke(
        config,
        [
            "update",
            entry_id,
            "-k",
            "notes",
            "-f",
            "importance=7",
            "-f",
            'aliases=["x","y"]',
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output

    payload = _json_payload(_invoke(config, ["get", entry_id, "-k", "notes", "--format", "json"]))
    assert payload["importance"] == 7, payload

    frontmatter = list(kb_path.rglob("*.md"))[0].read_text(encoding="utf-8").split("---", 2)[1]
    assert load_yaml(frontmatter)["aliases"] == ["x", "y"]
