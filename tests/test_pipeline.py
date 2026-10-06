"""What goes into the private page and into the page meant for the web."""

from zotero_archive.extract import Item, Library
from zotero_archive.pipeline import Label, Options, _payload, _public_link
from zotero_archive.themes import Group


def item(**fields) -> Item:
    defaults = dict(key="ABCD1234", item_type="book", date_added="2012-03-01T10:00:00Z", title="Un titre")
    return Item(**(defaults | fields))


def test_public_link_is_built_from_the_doi_only():
    assert _public_link(item(doi="10.1000/a b")) == "https://doi.org/10.1000/a%20b"
    assert _public_link(item(doi="https://doi.org/10.1000/xyz")) == "https://doi.org/10.1000/xyz"
    assert _public_link(item(doi="doi: 10.1000/xyz")) == "https://doi.org/10.1000/xyz"
    assert _public_link(item(doi="javascript:alert(1)")) == ""
    assert _public_link(item()) == ""


def payload(**options) -> dict:
    web = options.pop("web", False)
    items = [
        item(creators="Schacht", year=1936, doi="10.1000/xyz", collections=["Thèse"]),
        item(key="EFGH5678", date_added="2012-03-01T11:00:00Z", title="Sans lien"),
    ]
    group = dict(size=2, keywords=["monnaie"], exemplars=[0], collections=[("Thèse", 2)], tags=[])
    themes = [Group(id=0, children=[0], **group)]
    subthemes = [Group(id=0, parent=0, **group)]
    labels = {
        ("theme", 0): Label("Monnaie", "Monnaie", "ollama:test"),
        ("sub", 0): Label("Banques centrales", "monnaie", "keywords"),
    }
    library = Library(id=1, kind="user", name="Ma bibliothèque", group_id=None, n_items=2)
    return _payload(library, items, [0, 0], themes, subthemes, labels, Options(bulk_threshold=2, **options), web=web)


def test_private_page_opens_references_in_zotero():
    data = payload()
    assert data["linkPrefix"] == "zotero://select/library/items/"
    assert (data["themes"][0]["label"], data["subthemes"][0]["label"]) == ("Monnaie", "Banques centrales")
    assert data["labelModel"] == "test"
    assert data["items"][0][:4] == ["ABCD1234", "Un titre", "Schacht", 1936]
    assert data["themes"][0]["collections"] == [("Thèse", 2)]
    assert data["bulkDays"] == [("2012-03-01", 2)]


def test_web_page_keeps_only_what_the_charts_need_by_default():
    data = payload(web=True, name="Bibliothèque de test")
    assert data["library"] == "Bibliothèque de test"
    assert data["web"] and not data["references"] and data["linkPrefix"] == ""
    # Date, sub-theme and bulk flag: no title, author, key or link.
    assert data["items"] == [["", "", "", None, 0, "2012-03-01", 0, 1]] * 2
    assert data["themes"][0]["collections"] == [] and data["subthemes"][0]["collections"] == []
    assert "ABCD1234" not in str(data) and "Thèse" not in str(data) and "zotero://" not in str(data)


def test_web_page_can_list_references_with_public_links():
    data = payload(web=True, web_references=True)
    assert data["references"]
    assert data["items"][0] == ["", "Un titre", "Schacht", 1936, 0, "2012-03-01", 0, 1, "https://doi.org/10.1000/xyz"]
    assert data["items"][1][-1] == ""  # no DOI: the title is shown without a link
    assert "ABCD1234" not in str(data) and "Thèse" not in str(data) and "zotero://" not in str(data)
