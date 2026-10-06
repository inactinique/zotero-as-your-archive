"""Name themes with a language model served locally by Ollama.

The words picked by class-based TF-IDF describe a group without naming it. A
small local model, given those words and a few typical titles, proposes a short
label. The model is queried through Ollama's HTTP API on this machine, so the
library still does not leave it.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .themes import Group

DEFAULT_URL = "http://localhost:11434"

SYSTEM = (
    "Tu aides un chercheur à nommer les thèmes de sa bibliothèque de références bibliographiques. "
    "Pour le groupe de références décrit, propose un libellé court (2 à 6 mots) en français, précis "
    "et informatif, comme un intitulé de rayon de bibliothèque. Pas de guillemets, pas de point "
    "final, pas de formule vague comme « divers » ou « recherche »."
)
SCHEMA = {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}

MAX_LENGTH = 80


class LabellingError(RuntimeError):
    """Ollama cannot be reached, or does not have the requested model."""


def _call(url: str, path: str, body: dict | None = None, timeout: float = 300) -> dict:
    request = urllib.request.Request(
        url.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:300]
        raise LabellingError(f"Ollama a répondu par une erreur {error.code} : {detail}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        raise LabellingError(
            f"Ollama ne répond pas à l’adresse {url} ({getattr(error, 'reason', error)}). "
            "Lancez l’application Ollama (ou « ollama serve »), puis relancez la commande."
        ) from None


def check(model: str, url: str = DEFAULT_URL) -> None:
    """Fail early, before any long computation, if the model cannot be used."""
    installed = [m.get("name", "") for m in _call(url, "/api/tags", timeout=10).get("models", [])]
    if model not in installed and f"{model}:latest" not in installed:
        available = ", ".join(sorted(installed)) or "aucun"
        raise LabellingError(
            f"Le modèle « {model} » n’est pas installé dans Ollama (modèles disponibles : {available}). "
            f"Installez-le avec « ollama pull {model} »."
        )


def describe(
    group: Group,
    titles: list[str],
    parts: list[Group] = (),
    parent: Group | None = None,
    others: list[Group] = (),
) -> str:
    """The description of a group handed to the model.

    ``parts`` are the sub-themes of a theme, ``parent`` the theme of a
    sub-theme, and ``others`` the neighbouring groups it must not be confused with.
    """
    lines = [
        f"Groupe de {group.size} références.",
        "Mots caractéristiques : " + ", ".join(group.keywords) + ".",
    ]
    if parent is not None:
        lines.append("Ce groupe fait partie d’un thème plus large : " + ", ".join(parent.keywords[:6]) + ".")
    if parts:
        lines.append("Sous-ensembles (nombre de références, mots) :")
        lines += [f"- {p.size} : {', '.join(p.keywords[:6])}" for p in parts]
    if group.collections:
        names = " ; ".join(f"{name} ({n})" for name, n in group.collections[:4])
        lines.append(f"Collections Zotero les plus présentes : {names}.")
    lines.append("Titres représentatifs :")
    lines += [f"- {title[:140]}" for title in titles]
    if others:
        neighbours = " | ".join(", ".join(o.keywords[:3]) for o in others)
        lines.append(f"Autres groupes voisins, à ne pas confondre avec celui-ci : {neighbours}.")
    return "\n".join(lines)


def clean(label: str) -> str:
    """Tidy a proposed label: one line, no quotes, no final period."""
    label = re.sub(r"\s+", " ", label).strip().strip("\"'«»“”‘’ ").rstrip(".").strip()
    return label[:MAX_LENGTH].rstrip()


def propose(model: str, description: str, url: str = DEFAULT_URL) -> str:
    """Ask the model for a label; an empty string means it gave nothing usable."""
    answer = _call(
        url,
        "/api/chat",
        {
            "model": model,
            "stream": False,
            "think": False,  # a label does not need a reasoning phase
            "format": SCHEMA,
            "options": {"temperature": 0, "seed": 42},  # same library, same labels
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": description},
            ],
        },
    )
    try:
        return clean(str(json.loads(answer["message"]["content"])["label"]))
    except (KeyError, TypeError, ValueError):
        return ""
