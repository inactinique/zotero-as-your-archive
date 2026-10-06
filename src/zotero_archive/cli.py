"""Command-line interface."""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from .embed import DEFAULT_MODEL
from .extract import DEFAULT_DB, list_libraries, open_snapshot
from .labels import DEFAULT_URL, LabellingError
from .pipeline import MAX_THEMES, Options, run


def _n_themes(value: str) -> int:
    n = int(value)
    if not 2 <= n <= MAX_THEMES:
        raise argparse.ArgumentTypeError(
            f"entre 2 et {MAX_THEMES} : au-delà, les couleurs ne se distinguent plus "
            "(le détail passe par les sous-thèmes)"
        )
    return n


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="zotero-archive",
        description="Lire une bibliothèque Zotero comme l’archive des intérêts de son propriétaire.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    def add_db(p: argparse.ArgumentParser) -> None:
        p.add_argument("--db", type=Path, default=DEFAULT_DB, help="chemin de zotero.sqlite (défaut : %(default)s)")

    libraries = commands.add_parser("libraries", help="lister les bibliothèques de la base Zotero")
    add_db(libraries)

    build = commands.add_parser("build", help="analyser une bibliothèque et générer la visualisation")
    add_db(build)
    build.add_argument("--library", help="nom ou identifiant d’une bibliothèque de groupe (défaut : bibliothèque personnelle)")
    build.add_argument("--out", type=Path, default=Path("output"), help="dossier de sortie (défaut : %(default)s)")
    build.add_argument("--themes", type=_n_themes, default=MAX_THEMES, help="nombre de thèmes (défaut : %(default)s)")
    build.add_argument("--subthemes", type=int, default=40, help="nombre de sous-thèmes (défaut : %(default)s)")
    build.add_argument("--model", default=DEFAULT_MODEL, help="modèle sentence-transformers (défaut : %(default)s)")
    build.add_argument("--exclude-collection", action="append", default=[], metavar="TEXTE",
                       help="écarter les références d’une collection dont le chemin contient TEXTE (répétable)")
    build.add_argument("--bulk-threshold", type=int, default=100, metavar="N",
                       help="un jour compte comme import en masse à partir de N ajouts (défaut : %(default)s)")
    build.add_argument("--refit", action="store_true", help="recalculer les thèmes au lieu de reprendre les précédents")
    build.add_argument("--label-model", metavar="MODÈLE",
                       help="faire nommer les thèmes par un modèle de langue local servi par Ollama, par exemple qwen3:8b")
    build.add_argument("--ollama-url", default=DEFAULT_URL, metavar="URL", help="adresse d’Ollama (défaut : %(default)s)")
    build.add_argument("--name", metavar="TEXTE", help="nom affiché pour la bibliothèque, par exemple « Bibliothèque Zotero de … »")
    build.add_argument("--web", type=Path, metavar="DOSSIER",
                       help="écrire aussi dans DOSSIER une page publiable en ligne : sans liens vers Zotero, "
                            "sans noms de collections et sans liste des références")
    build.add_argument("--web-references", action="store_true",
                       help="avec --web : publier aussi la liste des références (titre, auteurs, année, lien)")
    build.add_argument("--open", action="store_true", help="ouvrir la page dans le navigateur")

    args = parser.parse_args(argv)
    if args.command == "build" and args.web_references and not args.web:
        parser.error("--web-references s’emploie avec --web")
    try:
        if args.command == "libraries":
            with open_snapshot(args.db) as con:
                for lib in list_libraries(con):
                    print(f"{lib.id:>4}  {lib.n_items:>6} références  {lib.name}")
            return
        page = run(
            Options(
                db=args.db, library=args.library, out=args.out, n_themes=args.themes,
                n_subthemes=args.subthemes, model_name=args.model, refit=args.refit,
                exclude=args.exclude_collection, bulk_threshold=args.bulk_threshold,
                name=args.name, web=args.web, web_references=args.web_references,
                label_model=args.label_model, ollama_url=args.ollama_url,
            )
        )
    except (FileNotFoundError, LookupError, LabellingError) as error:
        raise SystemExit(str(error)) from None
    print(f"\nPage générée : {page.resolve()}")
    print(f"Libellés modifiables : {(args.out / 'themes.json').resolve()}")
    if args.web:
        content = "graphiques et liste des références" if args.web_references else "graphiques seuls"
        print(f"Page pour le web ({content}) : {(args.web / 'index.html').resolve()}")
    if args.open:
        webbrowser.open(page.resolve().as_uri())
