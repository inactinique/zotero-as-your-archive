"""Group references into themes and sub-themes, and describe each group.

The recipe is the one popularised by BERTopic, kept explicit so that every
step can be inspected:

1. UMAP projects the embeddings to a few dimensions, preserving neighbourhoods;
2. k-means cuts that space into fine-grained sub-themes;
3. Ward's criterion merges the sub-themes, step by step, into broad themes;
4. class-based TF-IDF picks the words that set each group apart from the rest.
"""

from __future__ import annotations

import re
import unicodedata
import warnings
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

_TOKEN_RE = re.compile(r"[^\W\d_]{3,}", re.UNICODE)

# Languages whose function words are filtered out of the keywords.
STOPWORD_LANGUAGES = ("fr", "en", "de", "es", "it", "nl", "pt")

# Bibliographic noise that says nothing about the subject of a reference.
EXTRA_STOPWORDS = {
    "http", "https", "www", "doi", "org", "com", "html", "pdf", "isbn", "issn",
    "vol", "volume", "éd", "eds", "pp", "amp", "nbsp", "abstract", "résumé",
    "article", "paper", "chapter", "chapitre", "book", "livre", "ouvrage",
    "author", "authors", "auteur", "auteurs", "study", "étude",
}


@dataclass
class Group:
    """A theme or a sub-theme."""

    id: int
    size: int
    keywords: list[str]
    exemplars: list[int]  # indices of the most central references
    collections: list[tuple[str, int]]  # Zotero collections concentrated in the group
    tags: list[tuple[str, int]]
    parent: int | None = None  # theme id, for sub-themes
    children: list[int] = field(default_factory=list)  # sub-theme ids, for themes

    @property
    def auto_label(self) -> str:
        return " · ".join(self.keywords[:3]) or f"groupe {self.id + 1}"


@dataclass
class Model:
    """A fitted thematic model: centroids define sub-themes, ``parents`` their theme."""

    centroids: np.ndarray  # (n_subthemes, dim), L2-normalised
    parents: np.ndarray  # (n_subthemes,) theme id of each sub-theme

    @property
    def n_themes(self) -> int:
        return int(self.parents.max()) + 1


def fit(
    embeddings: np.ndarray,
    timestamps: np.ndarray,
    n_themes: int,
    n_subthemes: int,
    seed: int = 42,
) -> tuple[Model, np.ndarray]:
    """Fit themes on the embeddings; return the model and each item's sub-theme.

    Themes and sub-themes are numbered chronologically (by the median date at
    which their references were added), so that ids read as a timeline.
    """
    from sklearn.cluster import KMeans
    from umap import UMAP

    # Small libraries cannot support many groups: keep ~30 references per sub-theme.
    n_subthemes = max(2, min(n_subthemes, len(embeddings) // 30))
    n_themes = max(1, min(n_themes, n_subthemes))

    with warnings.catch_warnings():
        # A fixed seed makes the themes reproducible; UMAP warns that it then runs single-threaded.
        warnings.filterwarnings("ignore", message="n_jobs value", category=UserWarning)
        reduced = UMAP(
            n_components=5, n_neighbors=15, min_dist=0.0, metric="cosine", random_state=seed
        ).fit_transform(embeddings)
    sub = KMeans(n_clusters=n_subthemes, n_init=10, random_state=seed).fit_predict(reduced)

    sizes = np.bincount(sub, minlength=n_subthemes)
    means = np.vstack([embeddings[sub == k].mean(axis=0) for k in range(n_subthemes)])
    parents = _ward_merge(means, sizes, n_themes)

    # Renumber: themes by median date, then sub-themes by (theme, median date).
    theme_of_item = parents[sub]
    theme_rank = _rank([np.median(timestamps[theme_of_item == t]) for t in range(n_themes)])
    parents = theme_rank[parents]
    sub_median = [np.median(timestamps[sub == k]) for k in range(n_subthemes)]
    sub_rank = _rank(list(zip(parents.tolist(), sub_median)))
    order = np.argsort(sub_rank)
    model = Model(
        centroids=_normalise(means[order]),
        parents=parents[order],
    )
    return model, sub_rank[sub]


def assign(model: Model, embeddings: np.ndarray) -> np.ndarray:
    """Attach references to the nearest existing sub-theme (cosine similarity)."""
    return np.argmax(embeddings @ model.centroids.T, axis=1)


def _rank(keys: list) -> np.ndarray:
    """Position of each element once ``keys`` is sorted."""
    order = sorted(range(len(keys)), key=lambda i: keys[i])
    rank = np.empty(len(keys), dtype=int)
    rank[order] = np.arange(len(keys))
    return rank


def _normalise(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def _ward_merge(means: np.ndarray, sizes: np.ndarray, n_groups: int) -> np.ndarray:
    """Merge clusters until ``n_groups`` remain, using Ward's criterion.

    At each step the two clusters whose fusion least increases the within-group
    variance are merged. Unlike a plain hierarchical clustering of the
    centroids, this accounts for cluster sizes: small clusters get absorbed
    first, which keeps the broad themes comparable in weight.
    """
    mean = {k: m.astype(float) for k, m in enumerate(means)}
    size = {k: float(s) for k, s in enumerate(sizes)}
    members = {k: [k] for k in mean}
    while len(members) > n_groups:
        keys = list(members)
        _, a, b = min(
            (size[a] * size[b] / (size[a] + size[b]) * float(np.sum((mean[a] - mean[b]) ** 2)), a, b)
            for i, a in enumerate(keys)
            for b in keys[i + 1 :]
        )
        mean[a] = (mean[a] * size[a] + mean[b] * size[b]) / (size[a] + size[b])
        size[a] += size[b]
        members[a] += members.pop(b)
        del mean[b], size[b]
    parents = np.empty(len(means), dtype=int)
    for group, subs in enumerate(members.values()):
        parents[subs] = group
    return parents


def _stopwords() -> set[str]:
    import stopwordsiso

    words = set(EXTRA_STOPWORDS)
    for lang in STOPWORD_LANGUAGES:
        words |= stopwordsiso.stopwords(lang)
    return words


def _tokenize(text: str, stopwords: set[str]) -> list[str]:
    """Words and two-word phrases, e.g. "histoire", "histoire économique"."""
    words = _TOKEN_RE.findall(text.lower())
    terms = [w for w in words if w not in stopwords]
    terms += [
        f"{a} {b}" for a, b in zip(words, words[1:]) if a not in stopwords and b not in stopwords
    ]
    return terms


def _stem(word: str) -> str:
    """A crude cross-language stem: "européenne", "european", "europe" -> "europ"."""
    plain = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode()
    return plain[:5]


def _keywords(counts: list[Counter], n_keywords: int, min_count: int = 3) -> list[list[str]]:
    """Class-based TF-IDF: terms frequent in one group and rare in the others."""
    totals: Counter = Counter()
    for c in counts:
        totals.update(c)
    average_size = sum(totals.values()) / max(len(counts), 1)
    result = []
    for c in counts:
        size = max(sum(c.values()), 1)
        scored = sorted(
            (
                (tf / size * np.log1p(average_size / totals[term]), term)
                for term, tf in c.items()
                if tf >= min_count
            ),
            reverse=True,
        )
        chosen: list[str] = []
        for _, term in scored:
            if len(chosen) == n_keywords:
                break
            words = term.split()
            stems = {_stem(w) for w in words}
            if len(words) == 2:
                # A phrase replaces the single word it mostly accounts for
                # ("intelligence" -> "intelligence artificielle").
                single = next((k for k in chosen if " " not in k and _stem(k) in stems), None)
                if single is None:
                    if not any({_stem(w) for w in k.split()} == stems for k in chosen):
                        chosen.append(term)
                elif c[term] >= 0.5 * c[single]:
                    chosen[chosen.index(single)] = term
                    chosen = [k for k in chosen if k == term or " " in k or _stem(k) not in stems]
            elif not any(stems & {_stem(w) for w in k.split()} for k in chosen):
                chosen.append(term)
        result.append(chosen)
    return result


def _concentrated(values: list[list[str]], labels: np.ndarray, n_groups: int, top: int = 5):
    """Per group, the collections or tags it concentrates (at least 3 references)."""
    per_group = [Counter() for _ in range(n_groups)]
    overall: Counter = Counter()
    for vals, g in zip(values, labels):
        per_group[g].update(vals)
        overall.update(vals)
    sizes = np.bincount(labels, minlength=n_groups)
    result = []
    for g, counter in enumerate(per_group):
        # Favour names that are both common in the group and specific to it.
        scored = sorted(
            ((n / max(sizes[g], 1) * n / overall[name], n, name) for name, n in counter.items() if n >= 3),
            reverse=True,
        )
        result.append([(name, n) for _, n, name in scored[:top]])
    return result


def describe(
    embeddings: np.ndarray,
    sub_labels: np.ndarray,
    model: Model,
    texts: list[str],
    collections: list[list[str]],
    tags: list[list[str]],
    n_keywords: int = 10,
) -> tuple[list[Group], list[Group]]:
    """Build the description of every theme and sub-theme."""
    stopwords = _stopwords()
    tokens = [_tokenize(t, stopwords) for t in texts]
    theme_labels = model.parents[sub_labels]

    def build(labels: np.ndarray, n: int) -> list[Group]:
        counts = [Counter() for _ in range(n)]
        for toks, g in zip(tokens, labels):
            counts[g].update(toks)
        keywords = _keywords(counts, n_keywords)
        colls = _concentrated(collections, labels, n)
        tgs = _concentrated(tags, labels, n)
        groups = []
        for g in range(n):
            members = np.flatnonzero(labels == g)
            exemplars: list[int] = []
            if len(members):
                centroid = embeddings[members].mean(axis=0)
                exemplars = members[np.argsort(-(embeddings[members] @ centroid))[:5]].tolist()
            groups.append(
                Group(
                    id=g,
                    size=len(members),
                    keywords=keywords[g],
                    exemplars=exemplars,
                    collections=colls[g],
                    tags=tgs[g],
                )
            )
        return groups

    subthemes = build(sub_labels, len(model.parents))
    themes = build(theme_labels, model.n_themes)
    for s in subthemes:
        s.parent = int(model.parents[s.id])
        themes[s.parent].children.append(s.id)
    return themes, subthemes
