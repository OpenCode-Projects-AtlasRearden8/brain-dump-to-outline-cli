from brainDumpOutline.offline import (
    bucket_for,
    classify,
    dedupe,
    normalize,
    organize,
    parse_items,
)


def test_normalize_strips_bullets_and_markers():
    assert normalize("- buy printer ink") == "buy printer ink"
    assert normalize("* TODO: pay bill") == "pay bill"
    assert normalize("1) clean garage") == "clean garage"
    assert normalize("- [ ] email sam") == "email sam"
    assert normalize("  •  odd     spacing  ") == "odd spacing"


def test_parse_items_skips_headings_and_blank_lines():
    text = "# my dump\n\n- entry one\n## section\n\nentry two\n"
    assert parse_items(text) == ["entry one", "entry two"]


def test_dedupe_removes_case_and_space_dupes():
    items = ["Buy printer ink", "buy Printer  ink", "buy printer ink", "adopt a cat"]
    assert dedupe(items) == ["Buy printer ink", "adopt a cat"]


def test_dedupe_ignores_punctuation_and_update_prefix_variants():
    from brainDumpOutline.offline import normalize

    items = [normalize(i) for i in ["pay the water bill", "Update: pay the water bill!!", "email jan?!"]]
    assert dedupe(items) == ["pay the water bill", "email jan?!"]


def test_classify_decisions():
    assert classify("should i move the dentist appt?") == "decision"
    assert classify("is it worth switching banks?") == "decision"
    assert classify("which bank has no fees") == "decision"
    assert classify("keep or cancel the streaming bundle?") == "decision"


def test_classify_actions():
    for line in ("buy printer ink", "TODO: write chapter 4", "pay the water bill",
                 "call library", "renew passport", "clean the garage"):
        assert classify(line) == "action", line


def test_classify_ideas():
    assert classify("idea: podcast interview") == "idea"
    assert classify("a thing about voices") == "idea"


def test_bucket_for_topics():
    assert bucket_for("refill the medication") == "Health"
    assert bucket_for("pay the water bill") == "Money"
    assert bucket_for("clean the garage") == "Home"
    assert bucket_for("write chapter 4 draft") == "Work & Writing"
    assert bucket_for("call library about lost card") == "Errands & Ideas"
    assert bucket_for("wanderless musing") == "Everything Else"


def test_organize_full_pipeline(sample_dump):
    outline = organize(sample_dump.read_text(encoding="utf-8"))
    flattened = [item for group in outline.groups for item in group.items]
    assert flattened == [
        "random thought dump",
        "idea: podcast interview",
        "buy new printer ink",
        "call library about the lost card",
        "write chapter 4 outline",
        "email newsletter swap",
        "pay the water bill",
        "clean the garage",
    ]
    assert [group.title for group in outline.groups] == [
        "Everything Else",
        "Errands & Ideas",
        "Work & Writing",
        "Money",
        "Home",
    ]
    assert outline.decisions == [
        "should i move the dentist appt to thursday?",
        "is it worth switching banks?",
        "keep or cancel the streaming bundle?",
    ]
    assert outline.next_actions == [
        "buy new printer ink",
        "write chapter 4 outline",
        "pay the water bill",
    ]


def test_organize_groups_orders_topics_first_seen():
    outline = organize("- refill meds\n- tidy the laundry\n- draft the blurb")
    assert [g.title for g in outline.groups] == ["Health", "Home", "Work & Writing"]


def test_organize_falls_back_to_items_for_next_actions():
    outline = organize("just a thing about voices\nmy cat anchored the couch")
    assert outline.next_actions == ["just a thing about voices", "my cat anchored the couch"]


def test_organize_empty_text():
    outline = organize("")
    assert outline.groups == []
    assert outline.decisions == []
    assert outline.next_actions == []
