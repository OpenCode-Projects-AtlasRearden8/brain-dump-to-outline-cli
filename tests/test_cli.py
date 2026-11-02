import csv
import io
import json

import pytest

from brainDumpOutline import llm
from brainDumpOutline.cli import run
from brainDumpOutline.llm import LLMError
from brainDumpOutline.offline import organize
from brainDumpOutline.render import render, render_csv, render_markdown


def test_render_markdown_review_first_framing(sample_dump):
    outline = organize(sample_dump.read_text(encoding="utf-8"))
    text = render_markdown(outline, summary="dump.txt")
    assert "# Brain-Dump Outline" in text
    assert "Review before using" in text
    assert "## Decisions to Make" in text
    assert "## Next Three Actions" in text
    assert "### Money" in text
    assert "- [ ] should i move the dentist appt to thursday?" in text
    assert "1. buy new printer ink" in text


def test_render_markdown_empty_sections_get_notice():
    text = render_markdown(organize(""))
    assert "_No decisions spotted in the dump._" in text
    assert "_Nothing picked yet" in text


def test_render_csv_columns_and_types(sample_dump):
    outline = organize(sample_dump.read_text(encoding="utf-8"))
    text = render_csv(outline)
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert rows[0]["section"] == "Everything Else"
    assert rows[0]["type"] == "topic"
    actions = [r for r in rows if r["type"] == "action"]
    assert len(actions) == 3
    assert actions[0]["item"] == "buy new printer ink"
    decisions = [r for r in rows if r["type"] == "decision"]
    assert decisions[0]["item"] == "should i move the dentist appt to thursday?"


def test_render_dispatches_format():
    outline = organize("buy stamps")
    assert render(outline, "csv").startswith("section,")
    assert "## Topics" in render(outline, "markdown")


def test_cli_offline_run_to_stdout(sample_dump, monkeypatch, capsys):
    monkeypatch.setattr(llm, "chat_completion", lambda *a, **k: (_ for _ in ()).throw(AssertionError("llm called")))
    code = run([str(sample_dump), "--offline"])
    out = capsys.readouterr()
    assert code == 0
    assert "# Brain-Dump Outline" in out.out
    assert "Review before using" in out.out
    assert "fallback" in out.err or "Offline mode" in out.err


def test_cli_falls_back_when_endpoint_fails(sample_dump, monkeypatch, capsys):
    monkeypatch.setattr(llm, "chat_completion", lambda text, cfg: (_ for _ in ()).throw(LLMError("down")))
    code = run([str(sample_dump), "--base-url", "http://localhost:9999/v1", "--model", "m"])
    out = capsys.readouterr()
    assert code == 0
    assert "# Brain-Dump Outline" in out.out
    assert "falling back" in out.err


def test_cli_llm_path_with_mocked_response(sample_dump, monkeypatch, capsys):
    content = json.dumps(
        {
            "groups": [{"title": "Admin", "items": ["sort the mail pile"]}],
            "decisions": ["switch or keep banks?"],
            "next_actions": ["sort the mail pile", "call the bank", "answer the letter"],
        }
    )
    monkeypatch.setattr(llm, "chat_completion", lambda text, cfg: content)
    code = run([str(sample_dump), "--base-url", "http://localhost:11434/v1", "--model", "llama3.2"])
    out = capsys.readouterr()
    assert code == 0
    assert "### Admin" in out.out
    assert "switch or keep banks?" in out.out
    assert "1. sort the mail pile" in out.out


def test_cli_llm_required_but_missing(sample_dump, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run([str(sample_dump), "--llm"])
    assert exit_info.value.code == 2
    assert "--llm needs an endpoint" in capsys.readouterr().err


def test_cli_llm_required_and_fails(sample_dump, monkeypatch, capsys):
    monkeypatch.setattr(llm, "chat_completion", lambda text, cfg: (_ for _ in ()).throw(LLMError("dead")))
    with pytest.raises(SystemExit) as exit_info:
        run([str(sample_dump), "--llm", "--base-url", "http://x/v1", "--model", "m"])
    assert exit_info.value.code == 2
    assert "LLM path failed" in capsys.readouterr().err


def test_cli_missing_target_ends_gracefully(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run([str(tmp_path / "nope.txt")])
    assert exit_info.value.code == 2
    assert "not a file or folder" in capsys.readouterr().err


def test_cli_empty_folder(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run([str(tmp_path)])
    assert exit_info.value.code == 2
    assert "no note text" in capsys.readouterr().err


def test_cli_csv_output_to_file(tmp_path, monkeypatch, capsys):
    from brainDumpOutline import cli as cli_module

    monkeypatch.setattr(llm, "chat_completion", lambda text, cfg: (_ for _ in ()).throw(AssertionError()))
    destination = tmp_path / "tasks.csv"
    dump = tmp_path / "dump.md"
    dump.write_text("- pay the water bill", encoding="utf-8")
    code = run([str(dump), "--offline", "-f", "csv", "-o", str(destination)])
    assert code == 0
    text = destination.read_text(encoding="utf-8")
    assert text.startswith("section,order,item,type,done")
    rows = list(csv.DictReader(io.StringIO(text)))
    assert rows[0]["item"] == "pay the water bill"


def test_cli_folder_of_notes(tmp_path, monkeypatch, capsys):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "a.md").write_text("- buy stamps\n- refill meds?", encoding="utf-8")
    (notes / "b.txt").write_text("call the library", encoding="utf-8")
    monkeypatch.setattr(llm, "chat_completion", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    code = run([str(notes), "--offline"])
    assert code == 0
    out = capsys.readouterr().out
    assert "buy stamps" in out
    assert "call the library" in out
    assert "## Topics" in out


def test_config_file_drives_format_and_endpoint(tmp_path, sample_dump, monkeypatch, capsys):
    cfg_file = tmp_path / "bd2outline.toml"
    cfg_file.write_text(
        "\n".join(
            [
                "[llm]",
                'base_url = "http://localhost:11434/v1"',
                'model = "llama3.2"',
                "",
                "[output]",
                'format = "csv"',
            ]
        ),
        encoding="utf-8",
    )
    dump = sample_dump
    monkeypatch.setattr(
        llm, "chat_completion", lambda text, cfg: (_ for _ in ()).throw(AssertionError())
    )
    code = run([str(dump), "--offline", "--config", str(cfg_file)])
    out = capsys.readouterr()
    assert code == 0
    assert out.out.startswith("section,")
