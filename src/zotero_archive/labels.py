"""Name themes with a language model served locally by Ollama.

The words picked by class-based TF-IDF describe a group without naming it. A
small local model, given those words and a few typical titles, proposes a short
label. The model is queried through Ollama's HTTP API on this machine, so the
library still does not leave it.
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.error
import urllib.request

from .themes import Group

DEFAULT_URL = "http://localhost:11434"
DEFAULT_LANGUAGE = "fr"
MAX_LENGTH = 80

# Languages that can be asked for by code. Any other value is handed to the
# model as it was written ("Polish", "Luxembourgish"...).
LANGUAGES = {
    "fr": "French",
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "nl": "Dutch",
    "pt": "Portuguese",
}
_ALIASES = {
    "français": "fr", "francais": "fr",
    "anglais": "en",
    "allemand": "de", "deutsch": "de",
    "espagnol": "es", "español": "es",
    "italien": "it", "italiano": "it",
    "néerlandais": "nl", "nederlands": "nl",
    "portugais": "pt", "português": "pt",
}
_ALIASES |= {name.lower(): code for code, name in LANGUAGES.items()}

# French, the language of most libraries this was written for, has its own
# prompt: asked in French, a small model writes better French labels.
SYSTEM_FR = (
    "Tu aides un chercheur à nommer les thèmes de sa bibliothèque de références bibliographiques. "
    "Pour le groupe de références décrit, propose un libellé court (2 à 6 mots) en français, précis "
    "et informatif, comme un intitulé de rayon de bibliothèque. Pas de guillemets, pas de point "
    "final, pas de formule vague comme « divers » ou « recherche »."
)
# For any other language the prompt is in English, and insists on the target
# language: small models otherwise slip into the language of the titles.
SYSTEM_OTHER = (
    "You help a researcher name the themes of their library of bibliographic references. "
    "For the group of references described, propose a short label (2 to 6 words) in {language}, "
    "precise and informative, like the heading of a library shelf. No quotation marks, no final "
    "period, no list of words separated by commas, no vague wording such as \"miscellaneous\" or "
    "\"research\". The words and titles you are given may be in other languages: do not copy "
    "them, write the label in {language}."
)
_PHRASES = {
    "fr": {
        "group": "Groupe de {n} références.",
        "words": "Mots caractéristiques : {words}.",
        "parent": "Ce groupe fait partie d’un thème plus large : {words}.",
        "parts": "Sous-ensembles (nombre de références, mots) :",
        "part": "- {n} : {words}",
        "collections": "Collections Zotero les plus présentes : {names}.",
        "titles": "Titres représentatifs :",
        "others": "Autres groupes voisins, à ne pas confondre avec celui-ci : {names}.",
    },
    "other": {
        "group": "Group of {n} references.",
        "words": "Distinctive words: {words}.",
        "parent": "This group belongs to a broader theme: {words}.",
        "parts": "Subsets (number of references, words):",
        "part": "- {n}: {words}",
        "collections": "Most frequent Zotero collections: {names}.",
        "titles": "Typical titles:",
        "others": "Neighbouring groups, not to be confused with this one: {names}.",
        "reminder": "\nLabel for this group, in {language}:",
    },
}


class LabellingError(RuntimeError):
    """Ollama cannot be reached, or does not have the requested model."""


def language_key(value: str) -> str:
    """Normalise a requested language: "EN", "English" and "anglais" all give "en"."""
    key = " ".join(value.split()).lower()
    if not key:
        raise ValueError("langue vide")
    return key if key in LANGUAGES else _ALIASES.get(key, key)


def language_name(key: str) -> str:
    """The name given to the model: "English" for "en", the value itself if unknown."""
    return LANGUAGES.get(key, key)


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
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """The description of a group handed to the model.

    ``parts`` are the sub-themes of a theme, ``parent`` the theme of a
    sub-theme, and ``others`` the neighbouring groups it must not be confused with.
    """
    say = _PHRASES["fr" if language == "fr" else "other"]
    lines = [
        say["group"].format(n=group.size),
        say["words"].format(words=", ".join(group.keywords)),
    ]
    if parent is not None:
        lines.append(say["parent"].format(words=", ".join(parent.keywords[:6])))
    if parts:
        lines.append(say["parts"])
        lines += [say["part"].format(n=p.size, words=", ".join(p.keywords[:6])) for p in parts]
    if group.collections:
        names = " ; ".join(f"{name} ({n})" for name, n in group.collections[:4])
        lines.append(say["collections"].format(names=names))
    lines.append(say["titles"])
    lines += [f"- {title[:140]}" for title in titles]
    if others:
        names = " | ".join(", ".join(o.keywords[:3]) for o in others)
        lines.append(say["others"].format(names=names))
    if "reminder" in say:
        lines.append(say["reminder"].format(language=language_name(language)))
    return "\n".join(lines)


def clean(label: str) -> str:
    """Tidy a proposed label: one line, no quotes, no final period, a capital first."""
    label = re.sub(r"\s+", " ", label).strip().strip("\"'«»“”‘’ ").rstrip(".").strip()
    return (label[:1].upper() + label[1:MAX_LENGTH]).rstrip()


def _answer_field(language: str) -> str:
    """The JSON field the model must fill: naming the language in it helps it comply."""
    if language == "fr":
        return "label"
    plain = unicodedata.normalize("NFKD", language_name(language)).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z]+", "_", plain.lower()).strip("_")
    return f"label_in_{slug}" if slug else "label"


def propose(
    model: str, description: str, url: str = DEFAULT_URL, language: str = DEFAULT_LANGUAGE
) -> str:
    """Ask the model for a label; an empty string means it gave nothing usable."""
    field = _answer_field(language)
    system = SYSTEM_FR if language == "fr" else SYSTEM_OTHER.format(language=language_name(language))
    answer = _call(
        url,
        "/api/chat",
        {
            "model": model,
            "stream": False,
            "think": False,  # a label does not need a reasoning phase
            "format": {"type": "object", "properties": {field: {"type": "string"}}, "required": [field]},
            "options": {"temperature": 0, "seed": 42},  # same library, same labels
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": description},
            ],
        },
    )
    try:
        return clean(str(json.loads(answer["message"]["content"])[field]))
    except (KeyError, TypeError, ValueError):
        return ""
