"""Tests for pyrite.utils.yaml round-trip YAML utilities."""

import pytest

from pyrite.exceptions import FrontmatterError
from pyrite.utils.yaml import dump_yaml, dump_yaml_file, load_yaml, load_yaml_file


class TestLoadYaml:
    def test_load_simple(self):
        text = "title: Hello\ntags: [a, b]"
        result = load_yaml(text)
        assert result["title"] == "Hello"
        assert result["tags"] == ["a", "b"]

    def test_load_empty(self):
        result = load_yaml("")
        assert not result or result == {}

    def test_load_preserves_order(self):
        text = "z_field: 1\na_field: 2\nm_field: 3"
        result = load_yaml(text)
        keys = list(result.keys())
        assert keys == ["z_field", "a_field", "m_field"]

    def test_load_nested(self):
        text = "parent:\n  child: value\n  list:\n  - a\n  - b"
        result = load_yaml(text)
        assert result["parent"]["child"] == "value"
        assert result["parent"]["list"] == ["a", "b"]

    def test_load_result_is_dict_compatible(self):
        """CommentedMap should work like a dict."""
        text = "a: 1\nb: 2"
        result = load_yaml(text)
        # Standard dict operations
        assert "a" in result
        assert result.get("c", "default") == "default"
        assert len(result) == 2
        assert list(result.items()) == [("a", 1), ("b", 2)]

    def test_load_invalid_yaml_raises_frontmatter_error(self):
        """A YAML parse error becomes a clean FrontmatterError, not a raw ruamel
        traceback that crashes the entry loader."""
        with pytest.raises(FrontmatterError):
            load_yaml("a: [1, 2\nb: oops")  # unclosed flow sequence

    def test_load_scalar_raises_frontmatter_error(self):
        """Frontmatter that parses to a scalar (not a mapping) is rejected."""
        with pytest.raises(FrontmatterError):
            load_yaml("just a bare string, not a mapping")

    def test_load_list_raises_frontmatter_error(self):
        """Frontmatter that parses to a list (not a mapping) is rejected."""
        with pytest.raises(FrontmatterError):
            load_yaml("- a\n- b")


class TestDumpYaml:
    def test_dump_simple(self):
        data = {"title": "Hello", "tags": ["a", "b"]}
        result = dump_yaml(data)
        assert "title: Hello" in result
        assert "tags:" in result

    def test_dump_no_sort_keys(self):
        """Keys should preserve insertion order, not be sorted."""
        data = {"z": 1, "a": 2, "m": 3}
        result = dump_yaml(data)
        lines = [l for l in result.split("\n") if l.strip()]
        assert lines[0].startswith("z:")
        assert lines[1].startswith("a:")
        assert lines[2].startswith("m:")

    def test_dump_returns_string(self):
        data = {"key": "value"}
        result = dump_yaml(data)
        assert isinstance(result, str)

    def test_dump_no_trailing_newline(self):
        """dump_yaml should strip trailing newline."""
        data = {"key": "value"}
        result = dump_yaml(data)
        assert not result.endswith("\n")


class TestRoundTrip:
    def test_round_trip_preserves_content(self):
        """Load then dump should produce semantically identical output."""
        original = "title: Test Entry\ntype: note\ntags:\n- alpha\n- beta\ndate: '2024-01-15'"
        data = load_yaml(original)
        result = dump_yaml(data)
        reloaded = load_yaml(result)
        assert reloaded["title"] == "Test Entry"
        assert reloaded["type"] == "note"
        assert reloaded["tags"] == ["alpha", "beta"]

    def test_round_trip_preserves_quoting(self):
        """Quoted strings should stay quoted."""
        original = "date: '2024-01-15'\ntitle: \"Hello World\""
        data = load_yaml(original)
        result = dump_yaml(data)
        assert "'2024-01-15'" in result

    def test_round_trip_preserves_comments(self):
        """Comments should survive round-trip."""
        original = "# This is a comment\ntitle: Test\n# Another comment\ntags: []"
        data = load_yaml(original)
        result = dump_yaml(data)
        assert "# This is a comment" in result

    def test_round_trip_single_field_change(self):
        """Changing one field should only affect that field in output."""
        original = "title: Original\ntype: note\ntags:\n- alpha"
        data = load_yaml(original)
        data["title"] = "Changed"
        result = dump_yaml(data)
        assert "title: Changed" in result
        assert "type: note" in result
        assert "- alpha" in result

    def test_round_trip_preserves_key_order(self):
        """Key order should be preserved through round-trip."""
        original = "z_last: 1\na_first: 2\nm_middle: 3"
        data = load_yaml(original)
        result = dump_yaml(data)
        lines = [l for l in result.split("\n") if l.strip()]
        assert lines[0].startswith("z_last:")
        assert lines[1].startswith("a_first:")
        assert lines[2].startswith("m_middle:")


class TestFileOperations:
    def test_file_round_trip(self, tmp_path):
        original = {"title": "Test", "tags": ["a", "b"]}
        path = tmp_path / "test.yaml"
        dump_yaml_file(original, path)
        loaded = load_yaml_file(path)
        assert loaded["title"] == "Test"
        assert loaded["tags"] == ["a", "b"]

    def test_load_yaml_file_empty(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("")
        result = load_yaml_file(path)
        assert not result or result == {}

    def test_dump_yaml_file_creates_file(self, tmp_path):
        path = tmp_path / "new.yaml"
        dump_yaml_file({"key": "value"}, path)
        assert path.exists()
        content = path.read_text()
        assert "key: value" in content


class TestBlockSequenceIndentRoundTrip:
    """A no-op load -> save keeps the block-sequence indentation it found (#148).

    ruamel's emitter takes `sequence`/`offset` for the whole document, so the
    numbers come from the parsed tree's line/column records.
    """

    def test_indented_links_block_is_kept(self):
        src = 'links:\n  - target: "adr-0018"\n    relation: "implements"\n'
        assert dump_yaml(load_yaml(src)) + "\n" == src

    def test_flush_links_block_is_kept(self):
        src = 'links:\n- target: "adr-0018"\n'
        assert dump_yaml(load_yaml(src)) + "\n" == src

    def test_indented_scalar_sequence_is_kept(self):
        src = "tags:\n  - a\n  - b\n"
        assert dump_yaml(load_yaml(src)) + "\n" == src

    def test_a_nested_sequence_reads_its_own_parent_column(self):
        src = "meta:\n  links:\n    - target: x\n"
        assert dump_yaml(load_yaml(src)) + "\n" == src

    def test_a_freshly_built_mapping_keeps_the_default_style(self):
        # No source document, so no style to preserve: pyrite's own default
        # stays exactly as it was, which is what keeps this change from
        # rewriting files nobody edited.
        assert dump_yaml({"links": [{"target": "x"}]}) == "links:\n- target: x"

    def test_a_document_that_mixes_both_styles_cannot_be_reproduced(self):
        """Recorded, not fixed: one setting per document means the first block
        sequence decides, and the other is re-indented."""
        src = "a:\n- x\nb:\n  - y\n"
        assert dump_yaml(load_yaml(src)) + "\n" == "a:\n- x\nb:\n- y\n"

    def test_dump_yaml_file_keeps_the_style_of_the_file_it_overwrites(self, tmp_path):
        path = tmp_path / "links.yaml"
        src = 'links:\n  - target: "x"\n'
        path.write_text(src)

        dump_yaml_file(load_yaml_file(path), path)

        assert path.read_text() == src
