"""Naming themes with a local language model, without a real model."""

import pytest

from zotero_archive import labels as labelling
from zotero_archive.extract import Item
from zotero_archive.pipeline import Options, _labels, _write_themes
from zotero_archive.themes import Group


def group(id, keywords, **fields) -> Group:
    defaults = dict(size=10, exemplars=[0], collections=[], tags=[])
    return Group(id=id, keywords=keywords, **(defaults | fields))


THEMES = [group(0, ["banque", "monnaie", "crise"], children=[0, 1]), group(1, ["twitter", "archives", "web"], children=[2])]
SUBTHEMES = [
    group(0, ["reichsbank", "schacht"], parent=0),
    group(1, ["franc", "poincaré"], parent=0, collections=[("Thèse", 4)]),
    group(2, ["tweets", "hashtag"], parent=1),
]
ITEMS = [Item(key="K", item_type="book", date_added="2010-01-01T00:00:00Z", title="Un titre représentatif")]


def test_clean_removes_quotes_final_period_and_line_breaks():
    assert labelling.clean(' « Banques centrales\n et   monnaie. » ') == "Banques centrales et monnaie"
    assert labelling.clean('"IA et histoire"') == "IA et histoire"
    assert labelling.clean("memory and history") == "Memory and history"
    assert len(labelling.clean("mot " * 100)) <= labelling.MAX_LENGTH


def test_description_of_a_theme_lists_its_parts_and_its_neighbours():
    text = labelling.describe(THEMES[0], ["Titre A"], parts=SUBTHEMES[:2], others=THEMES[1:])
    assert "banque, monnaie, crise" in text
    assert "- 10 : reichsbank, schacht" in text and "- 10 : franc, poincaré" in text
    assert "- Titre A" in text
    assert "à ne pas confondre avec celui-ci : twitter, archives, web" in text


def test_description_of_a_subtheme_names_its_theme_and_collections():
    text = labelling.describe(SUBTHEMES[1], ["Titre B"], parent=THEMES[0], others=SUBTHEMES[:1])
    assert "fait partie d’un thème plus large : banque, monnaie, crise" in text
    assert "Thèse (4)" in text
    assert "Sous-ensembles" not in text


def test_language_can_be_given_by_code_or_by_name():
    assert [labelling.language_key(v) for v in ("EN", "English", " anglais ", "de", "Deutsch")] == ["en", "en", "en", "de", "de"]
    assert labelling.language_name("en") == "English"
    # An unlisted language is handed to the model as written.
    assert labelling.language_key("Polish") == "polish" and labelling.language_name("polish") == "polish"
    with pytest.raises(ValueError):
        labelling.language_key("  ")


def test_description_in_another_language_is_in_english_and_restates_the_language():
    text = labelling.describe(SUBTHEMES[1], ["Titre B"], parent=THEMES[0], others=SUBTHEMES[:1], language="de")
    assert "Distinctive words: franc, poincaré." in text
    assert "belongs to a broader theme: banque, monnaie, crise" in text
    assert text.endswith("Label for this group, in German:")
    assert "Mots caractéristiques" not in text


def test_propose_asks_for_the_requested_language(monkeypatch):
    sent = []

    def fake_call(url, path, body=None, timeout=300):
        sent.append(body)
        field = body["format"]["required"][0]
        return {"message": {"content": '{"%s": "Central banks"}' % field}}

    monkeypatch.setattr(labelling, "_call", fake_call)
    assert labelling.propose("modele", "description", language="en") == "Central banks"
    assert labelling.propose("modele", "description", language="fr") == "Central banks"
    english, french = sent
    assert english["format"]["required"] == ["label_in_english"]
    assert "write the label in English" in english["messages"][0]["content"]
    assert french["format"]["required"] == ["label"]
    assert "en français" in french["messages"][0]["content"]


def test_propose_reads_the_label_and_tolerates_a_useless_answer(monkeypatch):
    answers = iter(['{"label": "« Banques centrales. »"}', "pas du JSON", '{"autre": 1}'])
    sent = []

    def fake_call(url, path, body=None, timeout=300):
        sent.append((url, path, body))
        return {"message": {"content": next(answers)}}

    monkeypatch.setattr(labelling, "_call", fake_call)
    assert labelling.propose("modele", "description", "http://ollama") == "Banques centrales"
    assert labelling.propose("modele", "description") == ""
    assert labelling.propose("modele", "description") == ""
    url, path, body = sent[0]
    assert (url, path, body["model"], body["stream"]) == ("http://ollama", "/api/chat", "modele", False)
    assert body["messages"][-1] == {"role": "user", "content": "description"}


def test_check_reports_a_missing_model_and_an_unreachable_server(monkeypatch):
    monkeypatch.setattr(labelling, "_call", lambda *a, **k: {"models": [{"name": "qwen3:8b"}, {"name": "nomic:latest"}]})
    labelling.check("qwen3:8b")
    labelling.check("nomic")  # Ollama lists it as nomic:latest
    with pytest.raises(labelling.LabellingError, match="ollama pull absent"):
        labelling.check("absent")
    monkeypatch.undo()
    with pytest.raises(labelling.LabellingError, match="ne répond pas"):
        labelling.check("qwen3:8b", "http://127.0.0.1:9")  # nothing listens there


@pytest.fixture
def model(monkeypatch):
    """A stand-in for Ollama that numbers its answers and records what it was asked."""
    calls = []

    def fake_propose(name, description, url=None, language="fr"):
        calls.append((name, description, language))
        return f"Nom {len(calls)} ({name}, {language})"

    monkeypatch.setattr(labelling, "propose", fake_propose)
    return calls


def labels_for(path, keep=True, **options):
    labels = _labels(path, THEMES, SUBTHEMES, ITEMS, keep=keep, opts=Options(**options))
    _write_themes(path, THEMES, SUBTHEMES, labels, ITEMS)
    return labels


def test_without_a_model_labels_are_the_distinctive_words(tmp_path, model):
    labels = labels_for(tmp_path / "themes.json")
    assert labels["theme", 0].text == "banque · monnaie · crise"
    assert {lab.source for lab in labels.values()} == {"keywords"}
    assert model == []


def test_model_names_every_group_once_and_names_persist(tmp_path, model):
    path = tmp_path / "themes.json"
    labels = labels_for(path, label_model="m1")
    assert len(model) == 5  # two themes, three sub-themes
    assert labels["theme", 0].text == "Nom 1 (m1, fr)" and labels["sub", 2].source == "ollama:m1"
    # The theme is described with its parts, the sub-theme with its theme.
    assert "Sous-ensembles" in model[0][1] and "thème plus large" in model[2][1]

    # Later runs reuse the names, with or without the option: the model is not called again.
    assert labels_for(path, label_model="m1")["theme", 0].text == "Nom 1 (m1, fr)"
    assert labels_for(path)["theme", 0].text == "Nom 1 (m1, fr)"
    assert len(model) == 5


def test_another_language_renames_the_groups_and_is_remembered(tmp_path, model):
    import json

    path = tmp_path / "themes.json"
    labels_for(path, label_model="m1")
    labels = labels_for(path, label_model="m1", label_language="en")
    assert len(model) == 10
    assert labels["theme", 0].text == "Nom 6 (m1, en)" and labels["theme", 0].language == "en"
    # The description handed to the model is in English and names the language.
    assert model[5][1].endswith("Label for this group, in English:") and model[5][2] == "en"
    assert json.loads(path.read_text(encoding="utf-8"))["themes"][0]["label_language"] == "en"

    # English names persist without the options, and asking for English again calls nothing.
    assert labels_for(path)["theme", 0].text == "Nom 6 (m1, en)"
    labels_for(path, label_model="m1", label_language="en")
    assert len(model) == 10


def test_names_obtained_before_the_language_option_count_as_french(tmp_path, model):
    import json

    path = tmp_path / "themes.json"
    labels_for(path, label_model="m1")
    content = json.loads(path.read_text(encoding="utf-8"))
    for theme in content["themes"]:
        for entry in [theme] + theme["subthemes"]:
            del entry["label_language"]  # as written by the previous version
    path.write_text(json.dumps(content), encoding="utf-8")

    assert labels_for(path, label_model="m1")["theme", 0].text == "Nom 1 (m1, fr)"
    assert len(model) == 5


def test_a_label_rewritten_by_the_user_wins_over_any_proposal(tmp_path, model):
    import json

    path = tmp_path / "themes.json"
    labels_for(path, label_model="m1")
    content = json.loads(path.read_text(encoding="utf-8"))
    content["themes"][0]["label"] = "Histoire monétaire"
    path.write_text(json.dumps(content), encoding="utf-8")

    assert labels_for(path)["theme", 0].text == "Histoire monétaire"
    # Another model renames the groups, but not the one named by hand.
    labels = labels_for(path, label_model="m2")
    assert len(model) == 10
    assert labels["theme", 0].text == "Histoire monétaire" and labels["theme", 0].source == "ollama:m2"
    assert labels["theme", 1].text.endswith("(m2, fr)")


def test_recomputed_themes_start_from_scratch_and_keep_a_backup(tmp_path, model):
    path = tmp_path / "themes.json"
    labels_for(path, label_model="m1")
    labels = labels_for(path, keep=False)
    assert labels["theme", 0].text == "banque · monnaie · crise"
    assert (tmp_path / "themes.json.bak").is_file()


def test_an_empty_answer_falls_back_to_the_words_and_is_retried(tmp_path, monkeypatch):
    path = tmp_path / "themes.json"
    monkeypatch.setattr(labelling, "propose", lambda *a, **k: "")
    labels = labels_for(path, label_model="m1")
    assert labels["sub", 0].text == "reichsbank · schacht" and labels["sub", 0].source == "keywords"
    monkeypatch.setattr(labelling, "propose", lambda *a, **k: "Reichsbank")
    assert labels_for(path, label_model="m1")["sub", 0].text == "Reichsbank"
