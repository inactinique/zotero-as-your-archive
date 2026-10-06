"""Turn each reference into a vector with a multilingual sentence-embedding model.

A multilingual model places "histoire économique" and "economic history" close
to each other, so that themes are not split along language lines. Vectors are
cached on disk: only new or modified references are embedded on later runs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Abstracts are occasionally whole pasted articles; the model only reads the
# first few hundred tokens anyway.
MAX_CHARS = 2000


def _digest(model_name: str, text: str) -> str:
    return hashlib.sha1(f"{model_name}\n{text}".encode()).hexdigest()


def embed_texts(
    texts: list[str],
    cache_path: Path,
    model_name: str = DEFAULT_MODEL,
    verbose: bool = True,
) -> np.ndarray:
    """Return one L2-normalised vector per text, reusing cached vectors."""
    texts = [t[:MAX_CHARS] for t in texts]
    digests = [_digest(model_name, t) for t in texts]

    cached: dict[str, np.ndarray] = {}
    if cache_path.is_file():
        with np.load(cache_path) as data:
            cached = dict(zip(data["digests"].tolist(), data["vectors"]))

    missing = [i for i, d in enumerate(digests) if d not in cached]
    if missing:
        if verbose:
            print(f"  calcul des embeddings pour {len(missing)} références ({model_name})…")
        from sentence_transformers import SentenceTransformer  # slow import

        try:
            # Once downloaded, the model is loaded without contacting the network.
            model = SentenceTransformer(model_name, local_files_only=True)
        except OSError:
            if verbose:
                print("  téléchargement du modèle (une seule fois)…")
            model = SentenceTransformer(model_name)
        vectors = model.encode(
            [texts[i] for i in missing],
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=verbose,
        )
        for i, vector in zip(missing, vectors):
            cached[digests[i]] = vector.astype(np.float32)
    elif verbose:
        print("  embeddings repris du cache")

    result = np.vstack([cached[d] for d in digests])
    if missing:
        # Keep only the vectors still in use, so the cache does not grow forever.
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        unique = dict(zip(digests, result))
        np.savez_compressed(
            cache_path, digests=np.array(list(unique)), vectors=np.vstack(list(unique.values()))
        )
    return result
