import pytest

from brainDumpOutline.config import Config, load_config
from brainDumpOutline.gather import read_dump


def test_load_config_missing_file_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None)
    assert cfg == Config()


def test_load_config_parses_llm_and_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bd2outline.toml").write_text(
        "[llm]\n"
        'base_url = " http://localhost:11434/v1 "\n'
        'model = "llama3.2"\n'
        "timeout = 30\n"
        'api_key_env = "MY_KEY"\n'
        "[output]\n"
        'format = "csv"\n',
        encoding="utf-8",
    )
    cfg = load_config(None)
    assert cfg.base_url == "http://localhost:11434/v1"
    assert cfg.model == "llama3.2"
    assert cfg.timeout == 30
    assert cfg.api_key_env == "MY_KEY"
    assert cfg.fmt == "csv"


def test_load_config_bad_values_sanitize(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cfg.toml").write_text(
        '[llm]\ntimeout = "not a number"\n[output]\nformat = "yaml"\n',
        encoding="utf-8",
    )
    cfg = load_config(str(tmp_path / "cfg.toml"))
    assert cfg.timeout == 90
    assert cfg.fmt == "markdown"


def test_load_config_broken_toml_is_empty(tmp_path, monkeypatch):
    (tmp_path / "broken.toml").write_text("no = [closed", encoding="utf-8")
    cfg = load_config(str(tmp_path / "broken.toml"))
    assert cfg == Config()


def test_api_key_resolved_from_environment(monkeypatch):
    cfg = Config(api_key_env="TEST_KEY_NAME")
    monkeypatch.delenv("TEST_KEY_NAME", raising=False)
    assert cfg.api_key is None
    monkeypatch.setenv("TEST_KEY_NAME", "sk-fake")
    assert cfg.api_key == "sk-fake"


def test_gather_single_file(sample_dump):
    text = read_dump(str(sample_dump))
    assert "printer ink" in text


def test_gather_folder_collects_note_files(tmp_path):
    folder = tmp_path / "notes"
    folder.mkdir()
    (folder / "a.md").write_text("first note", encoding="utf-8")
    (folder / "junk.bin").write_text("ignore me", encoding="utf-8")
    (folder / "b.txt").write_text("second note", encoding="utf-8")
    (folder / "empty.md").write_text("", encoding="utf-8")
    text = read_dump(str(folder))
    assert "first note" in text
    assert "second note" in text
    assert "ignore me" not in text
    assert "[from note: a.md]" in text


def test_gather_folder_missing_is_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_dump(str(tmp_path / "nothing"))
