"""From a Zotero database to the interactive page: the whole chain."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import resources
from pathlib import Path
from urllib.parse import quote

import numpy as np

from . import labels as labelling
from . import themes as thematic
from .embed import DEFAULT_MODEL, embed_texts
from .extract import DEFAULT_DB, Item, Library, find_library, load_items, open_snapshot, select_link

MAX_THEMES = 8  # the palette cannot tell more than eight hues apart reliably
MIN_ITEMS = 60
PROJECT_URL = "https://github.com/inactinique/zotero-as-your-archive"

TYPE_LABELS = {
    "journalArticle": "article de revue",
    "newspaperArticle": "article de presse",
    "magazineArticle": "article de magazine",
    "book": "livre",
    "bookSection": "chapitre",
    "webpage": "page web",
    "blogPost": "billet de blog",
    "conferencePaper": "communication",
    "report": "rapport",
    "preprint": "prépublication",
    "thesis": "thèse",
    "document": "document",
    "manuscript": "manuscrit",
    "presentation": "présentation",
    "videoRecording": "vidéo",
    "audioRecording": "enregistrement audio",
    "podcast": "podcast",
    "radioBroadcast": "émission de radio",
    "tvBroadcast": "émission de télévision",
    "film": "film",
    "letter": "lettre",
    "interview": "entretien",
    "encyclopediaArticle": "article d’encyclopédie",
    "dictionaryEntry": "entrée de dictionnaire",
    "forumPost": "message de forum",
    "computerProgram": "logiciel",
    "dataset": "jeu de données",
    "map": "carte",
    "artwork": "œuvre",
    "statute": "texte de loi",
    "case": "décision de justice",
    "patent": "brevet",
}


@dataclass
class Options:
    db: Path = DEFAULT_DB
    library: str | None = None
    out: Path = Path("output")
    n_themes: int = MAX_THEMES
    n_subthemes: int = 40
    model_name: str = DEFAULT_MODEL
    refit: bool = False
    exclude: list[str] = field(default_factory=list)
    bulk_threshold: int = 100
    name: str | None = None  # display name of the library
    web: Path | None = None  # folder for the publishable page
    web_references: bool = False  # list individual references on that page
    label_model: str | None = None  # Ollama model asked to name the themes
    label_language: str = labelling.DEFAULT_LANGUAGE  # language of the names it proposes
    ollama_url: str = labelling.DEFAULT_URL


@dataclass
class Label:
    text: str  # shown on the page: the automatic proposal, unless the user rewrote it
    auto: str  # the automatic proposal
    source: str  # where the proposal comes from: "keywords" or "ollama:<model>"
    language: str = ""  # language asked of the model, when it made the proposal


def run(opts: Options) -> Path:
    """Analyse a library and write ``index.html`` and ``themes.json`` in ``opts.out``.

    With ``opts.web``, a second page meant for publication is written there.
    """
    if opts.label_model:
        labelling.check(opts.label_model, opts.ollama_url)
    print("Lecture de la base Zotero…")
    with open_snapshot(opts.db) as con:
        library = find_library(con, opts.library)
        items = load_items(con, library)
    n_read = len(items)
    if opts.exclude:
        patterns = [p.casefold() for p in opts.exclude]
        items = [
            it for it in items
            if not any(p in c.casefold() for p in patterns for c in it.collections)
        ]
    print(f"  {library.name} : {len(items)} références" + (f" ({n_read - len(items)} écartées)" if n_read != len(items) else ""))
    if len(items) < MIN_ITEMS:
        raise SystemExit(f"Il faut au moins {MIN_ITEMS} références pour dégager des thèmes.")

    cache = opts.out / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    print("Représentation des références…")
    embeddings = embed_texts([it.text for it in items], cache / "embeddings.npz", opts.model_name)

    print("Thèmes…")
    params = {
        "model": opts.model_name,
        "themes": opts.n_themes,
        "subthemes": opts.n_subthemes,
        "exclude": sorted(opts.exclude),
        "library": library.id,
    }
    model, sub, fitted = _load_or_fit(cache / "model.npz", items, embeddings, params, opts.refit)
    themes, subthemes = thematic.describe(
        embeddings, sub, model,
        [it.text for it in items], [it.collections for it in items], [it.tags for it in items],
    )
    labels = _labels(opts.out / "themes.json", themes, subthemes, items, keep=not fitted, opts=opts)
    _write_themes(opts.out / "themes.json", themes, subthemes, labels, items)
    for t in themes:
        print(f"  {t.id + 1}. {labels['theme', t.id].text} ({t.size})")

    page = opts.out / "index.html"
    described = (library, items, sub, themes, subthemes, labels, opts)
    _write_page(page, _payload(*described))
    if opts.web:
        opts.web.mkdir(parents=True, exist_ok=True)
        _write_page(opts.web / "index.html", _payload(*described, web=True))
    return page


def _write_page(path: Path, payload: dict) -> None:
    template = resources.files("zotero_archive").joinpath("template.html").read_text(encoding="utf-8")
    # "</" must not appear inside the <script> element that carries the data.
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    path.write_text(template.replace("__DATA__", data), encoding="utf-8")


def _public_link(item: Item) -> str:
    """A link anyone can follow: the DOI, when the reference has one.

    The address stored by Zotero is deliberately not published: it may point
    to a webmail, an intranet or a shared document, or carry an access token.
    """
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", item.doi, flags=re.IGNORECASE)
    if doi.startswith("10."):
        return "https://doi.org/" + quote(doi, safe="/:;().,_-")
    return ""


def _timestamps(items: list[Item]) -> np.ndarray:
    return np.array(
        [datetime.fromisoformat(it.date_added.replace("Z", "+00:00")).timestamp() for it in items]
    )


def _load_or_fit(path: Path, items: list[Item], embeddings: np.ndarray, params: dict, refit: bool):
    """Reuse the saved themes when possible, so that they stay stable over time.

    References already seen keep their sub-theme; new ones join the nearest
    sub-theme. Themes are only recomputed on request or when parameters change.
    """
    keys = [it.key for it in items]
    model = sub = None
    if path.is_file() and not refit:
        with np.load(path) as saved:
            if json.loads(str(saved["params"])) == params:
                model = thematic.Model(centroids=saved["centroids"], parents=saved["parents"])
                known = dict(zip(saved["keys"].tolist(), saved["sub"].tolist()))
                sub = np.array([known.get(k, -1) for k in keys])
                new = sub < 0
                if new.any():
                    sub[new] = thematic.assign(model, embeddings[new])
                    print(f"  {int(new.sum())} nouvelles références rattachées aux thèmes existants")
                else:
                    print("  thèmes repris du calcul précédent")
            else:
                print("  paramètres modifiés : les thèmes sont recalculés")
    fitted = model is None
    if fitted:
        model, sub = thematic.fit(embeddings, _timestamps(items), params["themes"], params["subthemes"])
    np.savez_compressed(
        path, centroids=model.centroids, parents=model.parents,
        keys=np.array(keys), sub=sub, params=json.dumps(params),
    )
    return model, sub, fitted


def _labels(
    path: Path, themes, subthemes, items: list[Item], keep: bool, opts: Options
) -> dict[tuple[str, int], Label]:
    """A label for every theme and sub-theme.

    The automatic proposal is the group's most distinctive words, or a name
    given by a local language model when ``opts.label_model`` is set. Names
    already obtained from a model are reused as long as the themes are, so the
    model is only called for groups it has not named yet in the requested
    language. Whatever the proposal, a label rewritten by the user in
    themes.json wins.
    """
    previous: dict[tuple[str, int], dict] = {}
    if path.is_file():
        if keep:
            for t in json.loads(path.read_text(encoding="utf-8")).get("themes", []):
                for kind, entry in [("theme", t)] + [("sub", s) for s in t.get("subthemes", [])]:
                    previous[kind, entry["id"]] = entry
        else:
            backup = path.with_name("themes.json.bak")
            shutil.copy2(path, backup)
            print(f"  ancien fichier de libellés conservé dans {backup}")

    wanted = f"ollama:{opts.label_model}" if opts.label_model else None
    groups = [("theme", t) for t in themes] + [("sub", s) for s in subthemes]
    proposals: dict[tuple[str, int], tuple[str, str, str]] = {}
    unnamed = []
    for kind, group in groups:
        old = previous.get((kind, group.id), {})
        source = old.get("label_source", "keywords")
        # Names obtained before the language could be chosen were asked for in French.
        language = old.get("label_language", labelling.DEFAULT_LANGUAGE)
        if wanted and (source, language) != (wanted, opts.label_language):
            unnamed.append((kind, group))
        elif source.startswith("ollama:") and old.get("auto_label"):
            proposals[kind, group.id] = (old["auto_label"], source, language)
        else:
            proposals[kind, group.id] = (group.auto_label, "keywords", "")

    for done, (kind, group) in enumerate(unnamed, start=1):
        progress = f"libellés proposés par {opts.label_model} ({opts.label_language})"
        print(f"\r  {progress} : {done}/{len(unnamed)}", end="", flush=True)
        if kind == "theme":
            context = dict(
                parts=[subthemes[s] for s in group.children],
                others=[t for t in themes if t is not group],
            )
        else:
            parent = themes[group.parent]
            context = dict(
                parent=parent,
                others=[subthemes[s] for s in parent.children if s != group.id],
            )
        titles = [items[i].title for i in group.exemplars]
        description = labelling.describe(group, titles, language=opts.label_language, **context)
        name = labelling.propose(opts.label_model, description, opts.ollama_url, opts.label_language)
        # Without a usable answer, keep the words; the model is asked again next time.
        proposals[kind, group.id] = (
            (name, wanted, opts.label_language) if name else (group.auto_label, "keywords", "")
        )
    if unnamed:
        print()

    labels = {}
    for key, (auto, source, language) in proposals.items():
        old = previous.get(key, {})
        edited = bool(old.get("label")) and old["label"] != old.get("auto_label")
        labels[key] = Label(old["label"] if edited else auto, auto, source, language)
    return labels


def _write_themes(path: Path, themes, subthemes, labels, items: list[Item]) -> None:
    def entry(kind: str, group) -> dict:
        label = labels[kind, group.id]
        return {
            "id": group.id,
            "label": label.text,
            "auto_label": label.auto,
            "label_source": label.source,
            **({"label_language": label.language} if label.language else {}),
            "size": group.size,
            "keywords": group.keywords,
            "collections": [f"{name} ({n})" for name, n in group.collections],
            "exemplars": [items[i].title for i in group.exemplars],
        }

    content = {
        "aide": (
            "Pour renommer un thème ou un sous-thème, modifiez son champ « label » puis relancez "
            "« zotero-archive build ». Vos libellés sont conservés tant que les thèmes ne sont pas "
            "recalculés (option --refit ou changement de paramètres). « auto_label » est la "
            "proposition automatique, « label_source » son origine et « label_language » la "
            "langue demandée au modèle : n’y touchez pas."
        ),
        "themes": [
            entry("theme", t) | {"subthemes": [entry("sub", subthemes[s]) for s in t.children]}
            for t in themes
        ],
    }
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _payload(
    library: Library, items, sub, themes, subthemes, labels, opts: Options, web: bool = False
) -> dict:
    """The data embedded in the page.

    The private page links each reference to the Zotero application. The web
    page carries no Zotero key, link or collection name, and lists individual
    references only on request; it always keeps the date and sub-theme of each
    addition, which the charts are computed from.
    """
    references = opts.web_references or not web
    per_day = Counter(it.date_added[:10] for it in items)
    bulk_days = {day: n for day, n in per_day.items() if n >= opts.bulk_threshold}
    types = sorted({it.item_type for it in items})
    type_index = {t: i for i, t in enumerate(types)}
    named_by = sorted({lab.source.split(":", 1)[1] for lab in labels.values() if lab.source.startswith("ollama:")})

    def row(it: Item, k: int) -> list:
        day = it.date_added[:10]
        counted = [day, int(k), int(day in bulk_days)]
        if not references:
            return ["", "", "", None, 0, *counted]
        described = [it.title, it.creators, it.year, type_index[it.item_type]]
        return ["", *described, *counted, _public_link(it)] if web else [it.key, *described, *counted]

    return {
        "library": opts.name or library.name,
        "generated": date.today().isoformat(),
        "model": opts.model_name.split("/")[-1],
        "labelModel": ", ".join(named_by),
        "project": PROJECT_URL,
        "web": web,
        "references": references,
        "linkPrefix": "" if web else select_link(library, ""),
        "bulkThreshold": opts.bulk_threshold,
        "bulkDays": sorted(bulk_days.items()),
        "types": types,
        "typeLabels": {t: TYPE_LABELS[t] for t in types if t in TYPE_LABELS},
        "themes": [
            {
                "id": t.id,
                "label": labels["theme", t.id].text,
                "keywords": t.keywords,
                "collections": [] if web else t.collections,
                "subs": t.children,
            }
            for t in themes
        ],
        "subthemes": [
            {
                "id": s.id,
                "theme": s.parent,
                "label": labels["sub", s.id].text,
                "keywords": s.keywords,
                "collections": [] if web else s.collections,
            }
            for s in subthemes
        ],
        # One compact row per reference, oldest addition first.
        "items": [row(it, k) for it, k in zip(items, sub)],
    }
