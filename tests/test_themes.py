"""Thematic model: merging, numbering, keywords."""

from collections import Counter

import numpy as np

from zotero_archive import themes as T


def test_ward_merge_absorbs_small_nearby_clusters_first():
    # Two large clusters far apart, each with a small satellite.
    means = np.array([[0.0, 0.0], [0.2, 0.0], [5.0, 0.0], [5.2, 0.0]])
    sizes = np.array([100, 5, 100, 5])
    parents = T._ward_merge(means, sizes, 2)
    assert parents[0] == parents[1] and parents[2] == parents[3]
    assert parents[0] != parents[2]


def test_fit_numbers_themes_chronologically_and_assign_is_consistent():
    rng = np.random.default_rng(0)
    # Three well-separated topics, each added during its own period.
    centres = np.eye(3, 16)
    embeddings, timestamps = [], []
    for k, period in enumerate([2_000, 1_000, 3_000]):  # topic 1 is the oldest
        points = centres[k] + rng.normal(scale=0.05, size=(80, 16))
        embeddings.append(points / np.linalg.norm(points, axis=1, keepdims=True))
        timestamps.append(period + rng.uniform(0, 100, size=80))
    embeddings, timestamps = np.vstack(embeddings), np.concatenate(timestamps)

    model, sub = T.fit(embeddings, timestamps, n_themes=3, n_subthemes=6)
    theme = model.parents[sub]
    # Each topic is one theme, and theme ids follow the order of addition.
    assert [int(np.bincount(theme[i : i + 80]).argmax()) for i in (0, 80, 160)] == [1, 0, 2]
    assert all(len(set(theme[i : i + 80])) == 1 for i in (0, 80, 160))
    # Sub-themes are numbered within their theme, themes in order.
    assert model.parents.tolist() == sorted(model.parents.tolist())
    # A new reference joins the theme of the nearest sub-theme.
    assert (model.parents[T.assign(model, embeddings)] == theme).all()


def test_tokenize_keeps_words_and_phrases_without_stopwords():
    terms = T._tokenize("L'histoire économique de la France en 1936", {"de", "la", "en"})
    assert "histoire économique" in terms and "france" in terms
    assert "de" not in terms and "économique de" not in terms and "1936" not in terms


def test_keywords_are_distinctive_and_not_redundant():
    counts = [
        Counter({"europe": 30, "european": 25, "européenne": 20, "histoire": 40, "intégration": 12}),
        Counter({"intelligence": 30, "intelligence artificielle": 28, "histoire": 40, "chatgpt": 9}),
    ]
    first, second = T._keywords(counts, 3)
    # One form per word family, across languages.
    assert first == ["europe", "histoire", "intégration"]
    # The phrase replaces the single word it mostly accounts for.
    assert second[0] == "intelligence artificielle" and "intelligence" not in second
