"""Shared pytest fixtures."""

import pytest


@pytest.fixture()
def sample_dump(tmp_path):
    path = tmp_path / "dump.txt"
    path.write_text(
        "\n".join(
            [
                "random thought dump",
                "",
                "- buy new printer ink",
                "  buy new printer ink  ",
                "TODO: write chapter 4 outline",
                "- should i move the dentist appt to thursday?",
                "is it worth switching banks?",
                "* pay the water bill",
                "1) clean the garage",
                "call library about the lost card",
                "- idea: podcast interview",
                "keep or cancel the streaming bundle?",
                "- old ideas: email newsletter swap",
            ]
        ),
        encoding="utf-8",
    )
    return path
