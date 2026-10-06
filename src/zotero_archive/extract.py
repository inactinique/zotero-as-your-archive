"""Read bibliographic items out of a local Zotero database.

Zotero keeps an exclusive lock on ``zotero.sqlite`` while it is running, so we
never open the live file: we work on a throw-away copy, opened read-only.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

DEFAULT_DB = Path.home() / "Zotero" / "zotero.sqlite"

# Item types that are not bibliographic references in their own right.
NON_REFERENCE_TYPES = ("attachment", "note", "annotation")

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_YEAR_RE = re.compile(r"(1[0-9]{3}|20[0-9]{2})")


@dataclass
class Library:
    id: int
    kind: str  # "user" or "group"
    name: str
    group_id: int | None
    n_items: int


@dataclass
class Item:
    key: str
    item_type: str
    date_added: str  # ISO 8601, UTC, as stored by Zotero
    title: str
    abstract: str = ""
    year: int | None = None  # publication year
    language: str = ""
    doi: str = ""
    creators: str = ""
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """The text that represents the item for thematic analysis."""
        return f"{self.title}. {self.abstract}".strip(" .") if self.abstract else self.title


@contextmanager
def open_snapshot(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open a private, read-only copy of the Zotero database."""
    db_path = Path(db_path).expanduser()
    if not db_path.is_file():
        raise FileNotFoundError(
            f"Base Zotero introuvable : {db_path}\n"
            "Indiquez son emplacement avec --db (voir Zotero > Paramètres > "
            "Avancées > Fichiers et dossiers > Emplacement du répertoire de données)."
        )
    with tempfile.TemporaryDirectory(prefix="zotero-archive-") as tmp:
        copy = Path(tmp) / "zotero.sqlite"
        shutil.copy2(db_path, copy)
        # Pending writes live in the write-ahead log; SQLite replays it on open.
        wal = db_path.with_name(db_path.name + "-wal")
        if wal.is_file() and wal.stat().st_size:
            shutil.copy2(wal, copy.with_name(copy.name + "-wal"))
        con = sqlite3.connect(copy)
        con.execute("PRAGMA query_only = ON")
        try:
            yield con
        finally:
            con.close()


def _reference_filter(alias: str = "i") -> str:
    types = ", ".join(f"'{t}'" for t in NON_REFERENCE_TYPES)
    return (
        f"{alias}.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ({types})) "
        f"AND {alias}.itemID NOT IN (SELECT itemID FROM deletedItems)"
    )


def list_libraries(con: sqlite3.Connection) -> list[Library]:
    """The personal library and the group libraries (RSS feeds are ignored)."""
    rows = con.execute(
        f"""
        SELECT l.libraryID, l.type, g.name, g.groupID,
               (SELECT count(*) FROM items i
                 WHERE i.libraryID = l.libraryID AND {_reference_filter()})
        FROM libraries l LEFT JOIN groups g USING (libraryID)
        WHERE l.type IN ('user', 'group')
        ORDER BY l.type = 'group', g.name
        """
    ).fetchall()
    return [
        Library(id=r[0], kind=r[1], name=r[2] or "Ma bibliothèque", group_id=r[3], n_items=r[4])
        for r in rows
    ]


def find_library(con: sqlite3.Connection, selector: str | None) -> Library:
    """Resolve ``--library``: nothing (personal library), a libraryID or a group name."""
    libraries = list_libraries(con)
    if selector is None:
        return next(lib for lib in libraries if lib.kind == "user")
    for lib in libraries:
        if selector == str(lib.id) or selector.casefold() == lib.name.casefold():
            return lib
    matches = [lib for lib in libraries if selector.casefold() in lib.name.casefold()]
    if len(matches) == 1:
        return matches[0]
    names = ", ".join(f"{lib.id} = {lib.name}" for lib in libraries)
    raise LookupError(f"Bibliothèque « {selector} » introuvable ou ambiguë. Disponibles : {names}")


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return _SPACE_RE.sub(" ", _TAG_RE.sub(" ", value)).strip()


def _collection_paths(con: sqlite3.Connection, library_id: int) -> dict[int, str]:
    """Map each collectionID to its full path, e.g. ``Thèse / Sources / Presse``."""
    rows = con.execute(
        "SELECT collectionID, collectionName, parentCollectionID FROM collections WHERE libraryID = ?",
        (library_id,),
    ).fetchall()
    names = {cid: name for cid, name, _ in rows}
    parents = {cid: parent for cid, _, parent in rows}
    paths: dict[int, str] = {}
    for cid in names:
        parts, cursor, seen = [], cid, set()
        while cursor is not None and cursor in names and cursor not in seen:
            seen.add(cursor)
            parts.append(names[cursor])
            cursor = parents[cursor]
        paths[cid] = " / ".join(reversed(parts))
    return paths


def load_items(con: sqlite3.Connection, library: Library) -> list[Item]:
    """All bibliographic references of a library, oldest addition first."""
    base = con.execute(
        f"""
        SELECT i.itemID, i.key, t.typeName, i.dateAdded
        FROM items i JOIN itemTypes t USING (itemTypeID)
        WHERE i.libraryID = ? AND {_reference_filter()}
        ORDER BY i.dateAdded, i.itemID
        """,
        (library.id,),
    ).fetchall()

    # Some item types store their title or date under a type-specific field
    # (caseName, dateEnacted...); baseFieldMappingsCombined maps them back.
    fields: dict[int, dict[str, str]] = defaultdict(dict)
    for item_id, name, value in con.execute(
        """
        SELECT d.itemID, coalesce(bf.fieldName, f.fieldName), v.value
        FROM itemData d
        JOIN items i USING (itemID)
        JOIN fields f USING (fieldID)
        JOIN itemDataValues v USING (valueID)
        LEFT JOIN baseFieldMappingsCombined m
               ON m.itemTypeID = i.itemTypeID AND m.fieldID = d.fieldID
        LEFT JOIN fields bf ON bf.fieldID = m.baseFieldID
        WHERE i.libraryID = ?
          AND coalesce(bf.fieldName, f.fieldName)
              IN ('title', 'abstractNote', 'date', 'language', 'DOI')
        """,
        (library.id,),
    ):
        fields[item_id][name] = value

    creators: dict[int, list[str]] = defaultdict(list)
    for item_id, last, first in con.execute(
        """
        SELECT ic.itemID, c.lastName, c.firstName
        FROM itemCreators ic JOIN creators c USING (creatorID) JOIN items i USING (itemID)
        WHERE i.libraryID = ? ORDER BY ic.itemID, ic.orderIndex
        """,
        (library.id,),
    ):
        creators[item_id].append(last or first or "")

    tags: dict[int, list[str]] = defaultdict(list)
    for item_id, name in con.execute(
        "SELECT it.itemID, t.name FROM itemTags it JOIN tags t USING (tagID) "
        "JOIN items i USING (itemID) WHERE i.libraryID = ?",
        (library.id,),
    ):
        tags[item_id].append(name)

    paths = _collection_paths(con, library.id)
    collections: dict[int, list[str]] = defaultdict(list)
    for item_id, collection_id in con.execute(
        "SELECT ci.itemID, ci.collectionID FROM collectionItems ci "
        "JOIN collections c USING (collectionID) WHERE c.libraryID = ?",
        (library.id,),
    ):
        collections[item_id].append(paths[collection_id])

    items = []
    for item_id, key, item_type, date_added in base:
        data = fields.get(item_id, {})
        title = _clean(data.get("title"))
        if not title:
            continue  # nothing to analyse
        year = _YEAR_RE.search(data.get("date", ""))
        names = [n for n in creators.get(item_id, []) if n]
        items.append(
            Item(
                key=key,
                item_type=item_type,
                date_added=date_added.replace(" ", "T") + "Z",
                title=title,
                abstract=_clean(data.get("abstractNote")),
                year=int(year.group(1)) if year else None,
                language=data.get("language", "").strip(),
                doi=data.get("DOI", "").strip(),
                creators=", ".join(names[:3]) + (" et al." if len(names) > 3 else ""),
                tags=sorted(tags.get(item_id, [])),
                collections=sorted(collections.get(item_id, [])),
            )
        )
    return items


def select_link(library: Library, key: str) -> str:
    """A link that opens the item in the Zotero desktop application."""
    scope = "library" if library.kind == "user" else f"groups/{library.group_id}"
    return f"zotero://select/{scope}/items/{key}"
