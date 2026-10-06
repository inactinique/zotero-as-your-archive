"""Extraction against a miniature database that follows Zotero's schema."""

import sqlite3

import pytest

from zotero_archive.extract import find_library, list_libraries, load_items, open_snapshot, select_link

SCHEMA = """
CREATE TABLE libraries (libraryID INTEGER PRIMARY KEY, type TEXT);
CREATE TABLE groups (groupID INTEGER PRIMARY KEY, libraryID INT, name TEXT);
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INT, dateAdded TEXT, libraryID INT, key TEXT);
CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY);
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
CREATE TABLE baseFieldMappingsCombined (itemTypeID INT, baseFieldID INT, fieldID INT);
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
CREATE TABLE itemCreators (itemID INT, creatorID INT, orderIndex INT);
CREATE TABLE tags (tagID INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE itemTags (itemID INT, tagID INT, type INT);
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT, parentCollectionID INT, libraryID INT);
CREATE TABLE collectionItems (collectionID INT, itemID INT);

INSERT INTO libraries VALUES (1, 'user'), (2, 'group'), (3, 'feed');
INSERT INTO groups VALUES (77, 2, 'Séminaire');
INSERT INTO itemTypes VALUES (1, 'book'), (2, 'note'), (3, 'attachment'), (4, 'case');
INSERT INTO fields VALUES (1, 'title'), (2, 'abstractNote'), (3, 'date'), (4, 'caseName'), (5, 'DOI');
INSERT INTO baseFieldMappingsCombined VALUES (4, 1, 4);

-- itemID, type, dateAdded, library, key
INSERT INTO items VALUES
  (1, 1, '2010-03-02 10:00:00', 1, 'BOOK0001'),
  (2, 1, '2008-06-05 09:10:49', 1, 'BOOK0002'),
  (3, 2, '2010-03-02 10:05:00', 1, 'NOTE0001'),
  (4, 3, '2010-03-02 10:06:00', 1, 'ATTACH01'),
  (5, 1, '2011-01-01 00:00:00', 1, 'TRASHED1'),
  (6, 4, '2012-01-01 00:00:00', 1, 'CASE0001'),
  (7, 1, '2012-02-01 00:00:00', 1, 'UNTITLED'),
  (8, 1, '2013-01-01 00:00:00', 2, 'GROUP001');
INSERT INTO deletedItems VALUES (5);
INSERT INTO itemDataValues VALUES
  (1, 'La Banque de France'), (2, '<p>Un résumé  avec <i>balises</i>.</p>'), (3, '1936-00-00 1936'),
  (4, 'Schacht'), (5, 'Supprimé'), (6, 'Arrêt Costa'), (7, 'Livre du groupe'),
  (8, '10.1000/banque');
INSERT INTO itemData VALUES (1, 1, 1), (1, 2, 2), (1, 3, 3), (2, 1, 4), (5, 1, 5), (6, 4, 6), (8, 1, 7),
  (1, 5, 8);
INSERT INTO creators VALUES (1, 'Hjalmar', 'Schacht'), (2, 'Émile', 'Moreau');
INSERT INTO itemCreators VALUES (1, 2, 1), (1, 1, 0);
INSERT INTO tags VALUES (1, 'monnaie');
INSERT INTO itemTags VALUES (1, 1, 0);
INSERT INTO collections VALUES (1, 'Thèse', NULL, 1), (2, 'Sources', 1, 1);
INSERT INTO collectionItems VALUES (2, 1);
"""


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "zotero.sqlite"
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.close()
    return path


def test_libraries_exclude_feeds_and_count_only_references(db):
    with open_snapshot(db) as con:
        libraries = list_libraries(con)
    assert [(lib.kind, lib.name, lib.n_items) for lib in libraries] == [
        ("user", "Ma bibliothèque", 4),
        ("group", "Séminaire", 1),
    ]


def test_items_are_references_with_a_title_in_order_of_addition(db):
    with open_snapshot(db) as con:
        items = load_items(con, find_library(con, None))
    # Notes, attachments, trashed and untitled items are left out.
    assert [it.key for it in items] == ["BOOK0002", "BOOK0001", "CASE0001"]


def test_item_fields(db):
    with open_snapshot(db) as con:
        items = {it.key: it for it in load_items(con, find_library(con, None))}
    book = items["BOOK0001"]
    assert book.title == "La Banque de France"
    assert book.abstract == "Un résumé avec balises ."
    assert book.year == 1936
    assert book.date_added == "2010-03-02T10:00:00Z"
    assert book.creators == "Schacht, Moreau"  # in the order set in Zotero
    assert book.tags == ["monnaie"]
    assert book.collections == ["Thèse / Sources"]
    assert book.doi == "10.1000/banque"
    # A type-specific title field (caseName) is read as the title.
    assert items["CASE0001"].title == "Arrêt Costa"


def test_group_library_lookup_and_links(db):
    with open_snapshot(db) as con:
        group = find_library(con, "séminaire")
        personal = find_library(con, None)
        assert [it.key for it in load_items(con, group)] == ["GROUP001"]
        with pytest.raises(LookupError):
            find_library(con, "inconnue")
    assert select_link(personal, "ABC") == "zotero://select/library/items/ABC"
    assert select_link(group, "ABC") == "zotero://select/groups/77/items/ABC"


def test_the_original_database_is_never_modified(db):
    before = db.read_bytes()
    with open_snapshot(db) as con:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("DELETE FROM items")
    assert db.read_bytes() == before


def test_missing_database_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        with open_snapshot(tmp_path / "absent.sqlite"):
            pass
