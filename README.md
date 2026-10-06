# Zotero as your archive · Zotero comme archive

**[English](#english)** · **[Français](#français)**

---

## English

A Zotero library keeps a trace of what caught its owner's attention: every
reference carries the date it was added. `zotero-archive` reads a library in
the order of those additions, groups the references into themes, and produces
an interactive page showing how the themes follow one another over the years.

Example, on a library started in 2008: <https://inactinique.net/zotero-archive/>

Everything runs on your computer. The Zotero database is copied and the copy is
read; your library is never modified. The model that represents your references
runs locally, and so does the optional one that names the themes: no data about
your library leaves your machine. The network is only used to install the
software and to download the models.

> The generated page and the command-line messages are in French for now. This
> guide quotes them in French and translates them. The names of the themes can
> be requested in another language.

**Contents**

1. [Quick start](#quick-start)
2. [What you need](#what-you-need)
3. [Installation](#installation)
4. [The first build](#the-first-build)
5. [The page, element by element](#the-page-element-by-element)
6. [The output folder, file by file](#the-output-folder-file-by-file)
7. [Naming the themes](#naming-the-themes)
8. [Everyday use](#everyday-use)
9. [Publishing the page on the web](#publishing-the-page-on-the-web)
10. [Command reference](#command-reference)
11. [How it works](#how-it-works)
12. [What stays private](#what-stays-private)
13. [Troubleshooting](#troubleshooting)
14. [Reusing and adapting the code](#reusing-and-adapting-the-code)
15. [Limits](#limits)
16. [Licence](#licence)

### Quick start

With [uv](https://docs.astral.sh/uv/), git and the Zotero desktop application
already installed:

```sh
git clone https://github.com/inactinique/zotero-as-your-archive.git
cd zotero-as-your-archive
uv run zotero-archive build --open
```

The first run downloads about 2 GB and takes a few minutes; the page then opens
in your browser. The rest of this guide explains each step and what you can
adjust.

### What you need

- The **Zotero desktop application**, with your library on this computer. The
  tool reads Zotero's local database; it does not use the zotero.org website.
- A library of **at least 60 references**. The more years it spans, the more
  there is to see.
- **[uv](https://docs.astral.sh/uv/)**, which installs Python and the
  dependencies for you, and **git**.
- About **2 GB of free disk space** (1 GB for the Python environment, 1 GB for
  the model that represents the references) and an internet connection for the
  installation and the first run.
- Optionally, **[Ollama](https://ollama.com)** with a model of your choice, to
  have the themes named by a local language model. Allow a few more gigabytes
  for that model.

Developed and tested on macOS (Apple Silicon) with Zotero 10. Nothing in the
code is specific to macOS, but Linux and Windows have not been tested.

### Installation

**1. Install uv**, if you do not have it.

```sh
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Get the code.**

```sh
git clone https://github.com/inactinique/zotero-as-your-archive.git
cd zotero-as-your-archive
```

All the commands of this guide are run from that folder. You do not need to
install Python or create an environment: `uv run` does it on first use.

**3. Check where Zotero keeps its data.** By default it is the `Zotero` folder
in your home directory (`~/Zotero`, or `C:\Users\<you>\Zotero` on Windows),
which contains a file named `zotero.sqlite`. If you moved it, the location is
shown in Zotero under *Settings → Advanced → Files and Folders → Data Directory
Location*; add `--db /path/to/zotero.sqlite` to the commands below.

To update the tool later, run `git pull` in the folder.

### The first build

```sh
uv run zotero-archive build --open
```

Zotero can stay open in the meantime. The command prints what it does:

```
Lecture de la base Zotero…
  Ma bibliothèque : 7440 références
Représentation des références…
  calcul des embeddings pour 7440 références (sentence-transformers/paraphrase-multilingual-mpnet-base-v2)…
Thèmes…
  1. central · banques · banking (293)
  2. france · diary · histoire (858)
  …
Page générée : …/output/index.html
Libellés modifiables : …/output/themes.json
```

| Line | Meaning |
| --- | --- |
| *Lecture de la base Zotero* | the database is copied and read; the number of references found is given |
| *Représentation des références* | each reference is turned into a vector; this is the long step of the first run |
| *Thèmes* | the themes, from the oldest to the most recent, with their number of references |
| *Page générée* | the path of the page |
| *Libellés modifiables* | the path of the file where themes can be renamed |

How long it takes, measured on a recent laptop with 7,400 references:

| Run | Duration |
| --- | --- |
| first build | the download of the model (about 1 GB), then about a minute and a half |
| later builds | about a second: only new references are processed |
| naming 48 groups with a local model | about a minute, once |

### The page, element by element

The page is a single file, `output/index.html`. It works offline, follows the
light or dark setting of your system, and adapts to narrow screens.

**The settings**, in one row at the top, apply to everything below:

- **Mesure** (measure): *Part des ajouts* shows each theme as a share of what
  was added during a period; *Nombre de références* shows counts.
- **Pas de temps** (time step): *Année* (year), *Semestre* (half-year) or
  *Trimestre* (quarter).
- **Écarter les imports en masse** (set aside bulk imports): hides the days
  when many references arrived at once, such as the import of an old database or
  of a press corpus, which otherwise flatten the rest of the period. The box
  only appears if such days exist; hover over it to see which days they are.

**Chart 1, "Ce qui entre dans la bibliothèque, période par période"** (what
enters the library, period by period). One column per period, split by theme,
the oldest theme at the top.

- As a share, all columns have the same height; the grey bars above them recall
  how many references were added, since a large share of a small volume weighs
  little.
- Hovering over a column lists every theme for that period, with its share and
  its count.
- Clicking a segment selects that theme and that period; clicking the same
  segment again releases the period.
- The legend on the left gives the number of references of each theme; clicking
  an entry selects the theme and dims the others.
- *Voir ces données sous forme de tableau* (see these data as a table) opens the
  same figures as a table.

**Chart 2, "Trajectoire de chaque thème"** (trajectory of each theme). One row
per theme, from the oldest to the most recent.

- Each row has its own vertical scale: it shows *when* a theme occupies the
  library. Its peak is marked and labelled, for instance `46 % · 2008`.
- Clicking the name of a theme unfolds its sub-themes, each with its own row.
- Clicking a curve selects the theme (or sub-theme) and the period under the
  pointer.

**"Références"**. The references matching the selection, from the oldest
addition to the most recent, a hundred at a time.

- The selection appears as removable labels, next to a menu for the period.
- When a theme is selected, its distinctive words and the Zotero collections
  most present in it are recalled.
- Each title opens the reference in the Zotero application.

### The output folder, file by file

Everything is written to `output/` (or to the folder given with `--out`). The
folder is ignored by git, because these files contain your library.

| File | What it is |
| --- | --- |
| `index.html` | the page, for your own use: its links open your Zotero |
| `themes.json` | the description of the themes; this is where you rename them |
| `themes.json.bak` | the previous `themes.json`, saved when the themes are recomputed |
| `.cache/embeddings.npz` | the vector of each reference, so that it is computed only once |
| `.cache/model.npz` | the themes themselves: which reference belongs to which sub-theme |

Deleting `.cache/` makes the next build start from scratch.

**`themes.json`** lists the themes in chronological order, each with its
sub-themes. The only field you are meant to edit is `label`.

| Field | Content |
| --- | --- |
| `id` | number of the theme, 0 being the oldest; it sets its colour and its position |
| `label` | the name shown on the page; **edit this one** |
| `auto_label` | the automatic proposal; if `label` differs from it, `label` is yours and is kept |
| `label_source` | where the proposal comes from: `keywords` or `ollama:<model>` |
| `label_language` | the language asked of the model, when a model proposed the name |
| `size` | number of references |
| `keywords` | the ten words or two-word phrases that best distinguish the group |
| `collections` | the Zotero collections most characteristic of the group, with their counts |
| `exemplars` | the titles of the five most typical references |
| `subthemes` | the sub-themes, with the same fields |

`size`, `keywords`, `collections` and `exemplars` are there to help you choose a
name; they are recomputed at every build, so editing them has no effect.

### Naming the themes

By default a theme is labelled with its three most distinctive words, for
instance `central · banques · banking`. This is often rough. There are two ways
to do better, and they combine.

#### With a local language model

[Install Ollama](https://ollama.com/download), start it, and download a model
once:

```sh
ollama pull qwen3:8b
```

Then ask for names:

```sh
uv run zotero-archive build --label-model qwen3:8b
```

For each theme and sub-theme, the model receives:

- the distinctive words of the group;
- for a theme, the words of its sub-themes; for a sub-theme, those of its theme;
- the Zotero collections most present in the group;
- the titles of its five most typical references;
- the words of the neighbouring groups, so as not to confuse them.

It answers with a name of two to six words. The model runs on your machine, so
your library still does not leave it.

**Language.** Names are in French by default. For another language, add
`--label-language` with a code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) or the
name of any other language:

```sh
uv run zotero-archive build --label-model qwen3:8b --label-language en
```

**The names are kept.** They are stored in `themes.json` and reused by later
builds, without calling the model. You only need these options again after
recomputing the themes, to try another model, or to change language.

**Which model.** Of the two models tried, `qwen3:8b` (5 GB) gave better names
than a smaller one of 3 GB, whose names were longer and less regular. Read the
proposals in any case: a small model is right most of the time, not always.

#### By hand

Open `output/themes.json`, change the `label` of a theme or a sub-theme, and run
the build command again. The words, collections and typical titles listed next
to each label help to choose it.

A label you wrote always wins: it is never replaced by a model's proposal, in
any language, as long as the themes are not recomputed.

### Everyday use

| I want to… | Command |
| --- | --- |
| build or update the page | `uv run zotero-archive build` |
| open it right away | add `--open` |
| take new references into account | run the same command again |
| get names from a local model | add `--label-model qwen3:8b` |
| get those names in English | add `--label-model qwen3:8b --label-language en` |
| rename a theme by hand | edit `label` in `output/themes.json`, then build again |
| leave out a collection of sources | add `--exclude-collection "name of the collection"` |
| have fewer themes | add `--themes 5` |
| have finer sub-themes | add `--subthemes 60` |
| start again from scratch | add `--refit` |
| show my name on the page | add `--name "Zotero library of Jane Doe"` |
| analyse a group library | `uv run zotero-archive libraries`, then add `--library "name" --out output-name` |
| publish the page | add `--web ../my-site/zotero-archive` |

A few things worth knowing:

- **Themes are frozen after the first computation.** References already
  classified keep their sub-theme, new ones join the nearest sub-theme, and
  your labels stay valid. A reference deleted from Zotero disappears from the
  page at the next build.
- **Changing the themes resets the labels.** `--refit`, `--themes`,
  `--subthemes`, `--model`, `--library` and `--exclude-collection` recompute
  the themes; the previous labels are saved in `themes.json.bak`, and the
  command says so (*paramètres modifiés : les thèmes sont recalculés*).
- **One output folder per library.** The cache belongs to one library and one
  set of options. To analyse a group library as well, give it its own folder
  with `--out`.
- **`--exclude-collection`** leaves out every reference filed in a collection
  whose path contains the text, whatever the case. The path includes parent
  collections, as in `Thesis / Sources / Press`. The option can be repeated.

### Publishing the page on the web

The page in `output/` is for you: its links open your own Zotero, and it
contains your item keys and collection names. To publish, ask for a second,
separate page:

```sh
uv run zotero-archive build --name "Zotero library of Jane Doe" --web ../my-site/zotero-archive
```

This writes `index.html` into the folder you name. By default that page
contains **the charts only**: themes, sub-themes, their names and distinctive
words, and the date and sub-theme of each addition. It contains no title,
author, Zotero key, link to Zotero, tag or collection name. Bear in mind that
the names and distinctive words are drawn from the titles and abstracts of your
references.

Add `--web-references` to also publish the list of references (title, first
authors, year, type, date added). Links are then limited to DOIs: the addresses
stored by Zotero are never published, as some point to webmails, intranets or
shared documents. Read the list before publishing it: a library often holds
internal or unpublished documents whose titles you may not want online.

The file is static and has no external dependency, so any web host will do. With
**GitHub Pages**, put the folder in the repository of your site, then commit and
push:

```sh
cd ../my-site
git add zotero-archive
git commit -m "Add the Zotero archive page"
git push
```

The page is then served at `https://<your-site>/zotero-archive/`. On a Jekyll
site the file is copied unchanged, since it has no front matter. If you have no
site yet, see [GitHub's documentation](https://docs.github.com/pages). To update
the published page, run the same build command again, then commit and push.

### Command reference

There are two commands. Both accept `--db PATH`, the location of
`zotero.sqlite` if it is not in `~/Zotero`.

**`uv run zotero-archive libraries`** lists the libraries of the database: an
identifier, the number of references and the name. Your personal library comes
first, then the group libraries.

**`uv run zotero-archive build`** analyses a library and writes the page. Its
options:

| Option | Effect | Default |
| --- | --- | --- |
| **What is analysed** | | |
| `--library NAME` | a group library, by its name, part of its name or its identifier | personal library |
| `--exclude-collection TEXT` | leave out the references of the collections whose path contains TEXT (repeatable) | none |
| **Themes** | | |
| `--themes N` | number of themes, from 2 to 8 | 8 |
| `--subthemes N` | number of sub-themes; never more than one per 30 references | 40 |
| `--model NAME` | the [sentence-transformers](https://www.sbert.net/) model that represents the references | `paraphrase-multilingual-mpnet-base-v2` |
| `--refit` | recompute the themes instead of reusing the previous ones | off |
| **Names** | | |
| `--label-model MODEL` | have the themes named by a model served by Ollama, e.g. `qwen3:8b` | distinctive words |
| `--label-language LANG` | with `--label-model`: language of the names, as a code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) or a language name | `fr` |
| `--ollama-url URL` | address of Ollama; if you point it at another machine, the descriptions of your themes are sent there | `http://localhost:11434` |
| **Page** | | |
| `--name TEXT` | name displayed for the library | *Ma bibliothèque*, or the name of the group |
| `--bulk-threshold N` | number of additions from which a day counts as a bulk import | 100 |
| `--open` | open the page in the browser | off |
| **Output** | | |
| `--out FOLDER` | output folder | `output` |
| `--web FOLDER` | also write a page for publication into FOLDER | none |
| `--web-references` | with `--web`: publish the list of references too | off |

What each kind of change costs:

| You change… | Vectors | Themes | Labels |
| --- | --- | --- | --- |
| nothing; references were added in Zotero | computed for the new ones | kept; new references join the nearest sub-theme | kept |
| `--label-model`, `--label-language` | kept | kept | the model's names are redone; yours are kept |
| `--name`, `--bulk-threshold`, `--web`, `--open` | kept | kept | kept |
| `--themes`, `--subthemes`, `--exclude-collection`, `--refit` | kept | recomputed | reset, with a backup |
| `--model`, `--library` | recomputed | recomputed | reset, with a backup |

### How it works

1. **Extraction** (`extract.py`). The database is copied to a temporary folder
   and the copy is opened read-only, which also works while Zotero is running.
   Every item that is not a note, an attachment or an annotation, is not in the
   trash and has a title is kept, with its title, abstract, date added, type,
   authors, publication year, DOI, tags and collections.
2. **Representation** (`embed.py`). Title and abstract are turned into a vector
   by a multilingual model
   ([paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2)),
   so that "histoire économique" and "economic history" end up close together.
   That model reads about the first hundred words: the title and the beginning
   of the abstract. Vectors are cached, so only new or modified references are
   computed again.
3. **Sub-themes** (`themes.py`). UMAP reduces the vectors to five dimensions,
   and k-means cuts that space into sub-themes.
4. **Themes**. The sub-themes are merged two by two, following Ward's
   criterion, until the requested number of themes remains. The criterion takes
   sizes into account: small sub-themes are absorbed first, which keeps the
   themes comparable in weight.
5. **Order**. Themes are numbered by the median date at which their references
   were added, and so are the sub-themes within each theme. This is what orders
   the legend and assigns the colours.
6. **Description**. For each group, a class-based TF-IDF picks the words and
   two-word phrases that are frequent in it and rare elsewhere, after removing
   the function words of seven languages and merging the variants of a same
   word across languages ("europe", "european", "européenne"). The typical
   references are the five closest to the centre of the group.
7. **Names** (`labels.py`, optional). A model served by Ollama names each group
   from that description.
8. **Page** (`template.html`). The data are embedded in one HTML file, which
   computes the charts in the browser.

Random steps use a fixed seed: on the same machine, the same library and the
same options give the same themes. Dates are those recorded by Zotero, in
universal time.

### What stays private

| | `output/index.html` | `--web` page | `--web` with `--web-references` |
| --- | --- | --- | --- |
| names and distinctive words of the themes | yes | yes | yes |
| date and sub-theme of each addition | yes | yes | yes |
| titles, authors, year, type | yes | no | yes |
| links | to your Zotero | none | DOI only |
| Zotero keys, collection names | yes | no | no |
| abstracts, tags, addresses, attachments | no | no | no |

`themes.json` and `.cache/` stay on your computer and are never part of a
published page. The only network connections are the installation, the download
of the models, and, if you use it, the address given with `--ollama-url`.

### Troubleshooting

| Message or symptom | Meaning | What to do |
| --- | --- | --- |
| *Base Zotero introuvable* | `zotero.sqlite` is not in `~/Zotero` | give its location with `--db` (see [Installation](#installation)) |
| *Il faut au moins 60 références pour dégager des thèmes* | the library, or what remains after `--exclude-collection`, is too small | analyse a larger library, or exclude less |
| *Bibliothèque « … » introuvable ou ambiguë* | no library, or several, match `--library` | run `zotero-archive libraries` and use the exact name or the identifier |
| *Ollama ne répond pas à l’adresse …* | Ollama is not running | start the Ollama application, or run `ollama serve` |
| *Le modèle « … » n’est pas installé dans Ollama* | the model was never downloaded | `ollama pull <model>`; the message lists the installed ones |
| *paramètres modifiés : les thèmes sont recalculés* | an option that defines the themes changed | nothing; your previous labels are in `themes.json.bak` |
| *--label-language s’emploie avec --label-model* | a language was given without a model | add `--label-model` |
| the first run seems stuck | the model (1 GB) is being downloaded | wait; later runs do not use the network |
| a title does not open Zotero | the `zotero://` links need the Zotero application on the same computer | open the page on the computer where Zotero is installed |
| the themes do not look right | the number of themes does not suit the library, or a corpus dominates it | try `--themes`, `--subthemes` or `--exclude-collection` |

To remove everything: delete the cloned folder, which contains the Python
environment and `output/`, and the model in
`~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-mpnet-base-v2`.

### Reusing and adapting the code

The code is small and each file has one job.

| File | Role | Main entry points |
| --- | --- | --- |
| `src/zotero_archive/extract.py` | read a Zotero database | `open_snapshot`, `list_libraries`, `find_library`, `load_items`, the `Item` class |
| `src/zotero_archive/embed.py` | turn texts into vectors, with a cache | `embed_texts` |
| `src/zotero_archive/themes.py` | group into themes and describe them | `fit`, `assign`, `describe` |
| `src/zotero_archive/labels.py` | name the groups with Ollama | `check`, `describe`, `propose` |
| `src/zotero_archive/pipeline.py` | chain the steps and write the files | `Options`, `run` |
| `src/zotero_archive/cli.py` | the command line | `main` |
| `src/zotero_archive/template.html` | the page: markup, styles and script in one file | |
| `tests/` | the tests | `uv run pytest` |

**Where to change what.**

| To change… | Look at |
| --- | --- |
| the texts of the page, or translate it | `template.html` |
| the colours | the `--s1` to `--s8` variables at the top of `template.html` |
| the instructions given to the naming model | `SYSTEM_FR` and `SYSTEM_OTHER` in `labels.py` |
| the languages whose function words are ignored | `STOPWORD_LANGUAGES` and `EXTRA_STOPWORDS` in `themes.py` |
| the names of the item types shown in the page | `TYPE_LABELS` in `pipeline.py` |
| the default model, or how much text it is given | `DEFAULT_MODEL` and `MAX_CHARS` in `embed.py` |
| which Zotero items count as references | `NON_REFERENCE_TYPES` in `extract.py` |

**Using the parts in your own script.** The extraction is useful on its own, for
instance in a notebook. This counts the references added each year:

```python
from collections import Counter

from zotero_archive.extract import DEFAULT_DB, find_library, load_items, open_snapshot

with open_snapshot(DEFAULT_DB) as con:
    library = find_library(con, None)  # None: your personal library
    items = load_items(con, library)

per_year = Counter(item.date_added[:4] for item in items)
for year, n in sorted(per_year.items()):
    print(year, n)
```

Each item has the fields `key`, `item_type`, `date_added`, `title`, `abstract`,
`year`, `language`, `doi`, `creators`, `tags` and `collections`. The whole chain
can also be run from Python, with the same options as the command line:

```python
from pathlib import Path

from zotero_archive.pipeline import Options, run

page = run(Options(out=Path("output-test"), n_themes=6, name="My library"))
```

Save a script in the folder of the project and run it with
`uv run python my_script.py`.

**Tests.** `uv run pytest` runs them in a few seconds. They use a miniature
Zotero database and a stand-in for Ollama, so they need neither your library
nor a model.

### Limits

- The date a reference was added is not the date it was read, and a bulk import
  gives a single date to references gathered over years.
- Only titles and abstracts are analysed. A reference without an abstract is
  classified on its title alone.
- Each reference belongs to one theme only, although a text may be about
  several.
- The grouping depends on the number of themes requested and on the model. It
  is a proposed reading, to be checked against what you know of your own
  library, not a result.
- Eight themes at most: beyond that, colours can no longer be told apart
  reliably. Sub-themes carry the detail.
- Names proposed by a language model are suggestions as well. A small model
  sometimes gets a group wrong, may give two groups the same name, and writes
  widely used languages better than others.
- The page and the messages of the command are in French only.

### Licence

[GNU General Public License v3.0 or later](LICENSE).

---

## Français

Une bibliothèque Zotero garde la trace de ce qui a retenu l'attention de son
propriétaire : chaque référence porte la date à laquelle elle a été ajoutée.
`zotero-archive` lit une bibliothèque dans l'ordre de ces ajouts, regroupe les
références en thèmes et produit une page interactive qui montre comment ces
thèmes se succèdent au fil des années.

Exemple, sur une bibliothèque ouverte en 2008 : <https://inactinique.net/zotero-archive/>

Tout se passe sur votre ordinateur. La base Zotero est copiée et c'est la copie
qui est lue ; votre bibliothèque n'est jamais modifiée. Le modèle qui représente
vos références tourne en local, tout comme celui, optionnel, qui nomme les
thèmes : aucune donnée sur votre bibliothèque ne quitte votre machine. Le réseau
ne sert qu'à installer le logiciel et à télécharger les modèles.

**Sommaire**

1. [Démarrage rapide](#démarrage-rapide)
2. [Ce qu'il vous faut](#ce-quil-vous-faut)
3. [Installer](#installer)
4. [La première génération](#la-première-génération)
5. [La page, élément par élément](#la-page-élément-par-élément)
6. [Le dossier de sortie, fichier par fichier](#le-dossier-de-sortie-fichier-par-fichier)
7. [Nommer les thèmes](#nommer-les-thèmes)
8. [Au quotidien](#au-quotidien)
9. [Publier la page sur le web](#publier-la-page-sur-le-web)
10. [Référence des commandes](#référence-des-commandes)
11. [Comment ça marche](#comment-ça-marche)
12. [Ce qui reste privé](#ce-qui-reste-privé)
13. [En cas de problème](#en-cas-de-problème)
14. [Réutiliser et adapter le code](#réutiliser-et-adapter-le-code)
15. [Limites](#limites)
16. [Licence](#licence-1)

### Démarrage rapide

Avec [uv](https://docs.astral.sh/uv/), git et l'application Zotero déjà
installés :

```sh
git clone https://github.com/inactinique/zotero-as-your-archive.git
cd zotero-as-your-archive
uv run zotero-archive build --open
```

La première exécution télécharge environ 2 Go et prend quelques minutes ; la
page s'ouvre ensuite dans votre navigateur. La suite de ce guide détaille chaque
étape et ce que vous pouvez régler.

### Ce qu'il vous faut

- L'**application Zotero** installée, avec votre bibliothèque sur cet
  ordinateur. L'outil lit la base locale de Zotero ; il n'utilise pas le site
  zotero.org.
- Une bibliothèque d'**au moins 60 références**. Plus elle couvre d'années, plus
  il y a à voir.
- **[uv](https://docs.astral.sh/uv/)**, qui installe Python et les dépendances
  à votre place, et **git**.
- Environ **2 Go d'espace disque** (1 Go pour l'environnement Python, 1 Go pour
  le modèle qui représente les références) et une connexion internet pour
  l'installation et la première exécution.
- En option, **[Ollama](https://ollama.com)** et un modèle de votre choix, pour
  faire nommer les thèmes par un modèle de langue local. Prévoyez quelques
  gigaoctets de plus pour ce modèle.

Développé et testé sous macOS (Apple Silicon) avec Zotero 10. Rien dans le code
n'est propre à macOS, mais Linux et Windows n'ont pas été testés.

### Installer

**1. Installez uv**, si vous ne l'avez pas.

```sh
# macOS et Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Récupérez le code.**

```sh
git clone https://github.com/inactinique/zotero-as-your-archive.git
cd zotero-as-your-archive
```

Toutes les commandes de ce guide se lancent depuis ce dossier. Vous n'avez ni à
installer Python ni à créer d'environnement : `uv run` s'en charge à la première
utilisation.

**3. Vérifiez où Zotero range ses données.** Par défaut, c'est le dossier
`Zotero` de votre répertoire personnel (`~/Zotero`, ou `C:\Users\<vous>\Zotero`
sous Windows), qui contient un fichier `zotero.sqlite`. Si vous l'avez déplacé,
son emplacement est indiqué dans Zotero, sous *Paramètres → Avancées → Fichiers
et dossiers → Emplacement du répertoire de données* ; ajoutez
`--db /chemin/vers/zotero.sqlite` aux commandes ci-dessous.

Pour mettre l'outil à jour par la suite, lancez `git pull` dans le dossier.

### La première génération

```sh
uv run zotero-archive build --open
```

Zotero peut rester ouvert pendant ce temps. La commande affiche ce qu'elle
fait :

```
Lecture de la base Zotero…
  Ma bibliothèque : 7440 références
Représentation des références…
  calcul des embeddings pour 7440 références (sentence-transformers/paraphrase-multilingual-mpnet-base-v2)…
Thèmes…
  1. central · banques · banking (293)
  2. france · diary · histoire (858)
  …
Page générée : …/output/index.html
Libellés modifiables : …/output/themes.json
```

| Ligne | Signification |
| --- | --- |
| *Lecture de la base Zotero* | la base est copiée puis lue ; le nombre de références trouvées est indiqué |
| *Représentation des références* | chaque référence est transformée en vecteur ; c'est l'étape longue de la première exécution |
| *Thèmes* | les thèmes, du plus ancien au plus récent, avec leur nombre de références |
| *Page générée* | le chemin de la page |
| *Libellés modifiables* | le chemin du fichier où renommer les thèmes |

Les durées, mesurées sur un portable récent avec 7 400 références :

| Exécution | Durée |
| --- | --- |
| première génération | le téléchargement du modèle (environ 1 Go), puis environ une minute et demie |
| générations suivantes | environ une seconde : seules les nouvelles références sont traitées |
| nommage de 48 groupes par un modèle local | environ une minute, une seule fois |

### La page, élément par élément

La page tient en un seul fichier, `output/index.html`. Elle fonctionne hors
ligne, suit le réglage clair ou sombre de votre système et s'adapte aux écrans
étroits.

**Les réglages**, sur une ligne en haut, s'appliquent à tout ce qui suit :

- **Mesure** : *Part des ajouts* montre chaque thème en proportion de ce qui a
  été ajouté pendant la période ; *Nombre de références* montre des effectifs.
- **Pas de temps** : *Année*, *Semestre* ou *Trimestre*.
- **Écarter les imports en masse** : masque les jours où beaucoup de références
  sont arrivées d'un coup, comme l'import d'une ancienne base ou d'un corpus de
  presse, qui écrasent sinon le reste de la période. La case n'apparaît que si
  de tels jours existent ; survolez-la pour voir lesquels.

**Graphique 1, « Ce qui entre dans la bibliothèque, période par période ».**
Une colonne par période, découpée selon les thèmes, le plus ancien en haut.

- En part des ajouts, toutes les colonnes ont la même hauteur ; les barres
  grises, au-dessus, rappellent combien de références ont été ajoutées, car une
  part élevée sur un petit volume pèse peu.
- Le survol d'une colonne détaille tous les thèmes de la période, avec leur part
  et leur effectif.
- Un clic sur un segment sélectionne ce thème et cette période ; un second clic
  sur le même segment libère la période.
- La légende, à gauche, donne le nombre de références de chaque thème ; un clic
  sur une entrée sélectionne le thème et atténue les autres.
- *Voir ces données sous forme de tableau* ouvre les mêmes chiffres en tableau.

**Graphique 2, « Trajectoire de chaque thème ».** Une ligne par thème, du plus
ancien au plus récent.

- Chaque ligne a sa propre échelle verticale : elle montre *quand* un thème
  occupe la bibliothèque. Son maximum est marqué et étiqueté, par exemple
  `46 % · 2008`.
- Un clic sur le nom d'un thème déplie ses sous-thèmes, chacun sur sa ligne.
- Un clic sur une courbe sélectionne le thème (ou le sous-thème) et la période
  située sous le pointeur.

**« Références ».** Les références correspondant à la sélection, de l'ajout le
plus ancien au plus récent, cent à la fois.

- La sélection apparaît sous forme d'étiquettes que l'on peut retirer, à côté
  d'un menu pour la période.
- Quand un thème est sélectionné, ses mots caractéristiques et les collections
  Zotero les plus présentes sont rappelés.
- Chaque titre ouvre la référence dans l'application Zotero.

### Le dossier de sortie, fichier par fichier

Tout est écrit dans `output/` (ou dans le dossier indiqué avec `--out`). Ce
dossier est ignoré par git, car ces fichiers contiennent votre bibliothèque.

| Fichier | Ce que c'est |
| --- | --- |
| `index.html` | la page, pour votre usage : ses liens ouvrent votre Zotero |
| `themes.json` | la description des thèmes ; c'est là qu'on les renomme |
| `themes.json.bak` | le `themes.json` précédent, sauvegardé quand les thèmes sont recalculés |
| `.cache/embeddings.npz` | le vecteur de chaque référence, pour ne le calculer qu'une fois |
| `.cache/model.npz` | les thèmes eux-mêmes : quelle référence appartient à quel sous-thème |

Supprimer `.cache/` fait repartir de zéro à la génération suivante.

**`themes.json`** liste les thèmes dans l'ordre chronologique, chacun avec ses
sous-thèmes. Le seul champ que vous êtes censé modifier est `label`.

| Champ | Contenu |
| --- | --- |
| `id` | numéro du thème, 0 étant le plus ancien ; il fixe sa couleur et sa position |
| `label` | le nom affiché sur la page ; **c'est celui-ci qu'on modifie** |
| `auto_label` | la proposition automatique ; si `label` en diffère, `label` est le vôtre et il est conservé |
| `label_source` | l'origine de la proposition : `keywords` ou `ollama:<modèle>` |
| `label_language` | la langue demandée au modèle, quand un modèle a proposé le nom |
| `size` | nombre de références |
| `keywords` | les dix mots ou expressions de deux mots qui distinguent le mieux le groupe |
| `collections` | les collections Zotero les plus caractéristiques du groupe, avec leur effectif |
| `exemplars` | les titres des cinq références les plus typiques |
| `subthemes` | les sous-thèmes, avec les mêmes champs |

`size`, `keywords`, `collections` et `exemplars` sont là pour vous aider à
choisir un nom ; ils sont recalculés à chaque génération, les modifier n'a donc
aucun effet.

### Nommer les thèmes

Par défaut, un thème est désigné par ses trois mots les plus caractéristiques,
par exemple `central · banques · banking`. C'est souvent approximatif. Il y a
deux façons de faire mieux, qui se combinent.

#### Avec un modèle de langue local

[Installez Ollama](https://ollama.com/download), lancez-le, et téléchargez un
modèle une fois pour toutes :

```sh
ollama pull qwen3:8b
```

Demandez ensuite des noms :

```sh
uv run zotero-archive build --label-model qwen3:8b
```

Pour chaque thème et sous-thème, le modèle reçoit :

- les mots caractéristiques du groupe ;
- pour un thème, les mots de ses sous-thèmes ; pour un sous-thème, ceux de son
  thème ;
- les collections Zotero les plus présentes dans le groupe ;
- les titres de ses cinq références les plus typiques ;
- les mots des groupes voisins, pour ne pas les confondre.

Il répond par un nom de deux à six mots. Le modèle s'exécute sur votre machine :
votre bibliothèque ne la quitte toujours pas.

**Langue.** Les noms sont en français par défaut. Pour une autre langue, ajoutez
`--label-language` suivi d'un code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) ou
du nom de n'importe quelle autre langue :

```sh
uv run zotero-archive build --label-model qwen3:8b --label-language en
```

**Les noms sont conservés.** Ils sont enregistrés dans `themes.json` et repris
par les générations suivantes, sans rappeler le modèle. Ces options ne
redeviennent nécessaires qu'après un recalcul des thèmes, pour essayer un autre
modèle ou pour changer de langue.

**Quel modèle.** Des deux modèles essayés, `qwen3:8b` (5 Go) a donné de
meilleurs noms qu'un modèle plus petit de 3 Go, dont les noms étaient plus longs
et moins réguliers. Relisez les propositions dans tous les cas : un petit modèle
a raison la plupart du temps, pas toujours.

#### À la main

Ouvrez `output/themes.json`, modifiez le `label` d'un thème ou d'un sous-thème,
puis relancez la commande. Les mots, les collections et les titres typiques
listés à côté de chaque libellé aident à le choisir.

Un libellé que vous avez écrit l'emporte toujours : il n'est jamais remplacé par
la proposition d'un modèle, dans aucune langue, tant que les thèmes ne sont pas
recalculés.

### Au quotidien

| Je veux… | Commande |
| --- | --- |
| générer ou mettre à jour la page | `uv run zotero-archive build` |
| l'ouvrir aussitôt | ajouter `--open` |
| prendre en compte de nouvelles références | relancer la même commande |
| obtenir des noms d'un modèle local | ajouter `--label-model qwen3:8b` |
| obtenir ces noms en anglais | ajouter `--label-model qwen3:8b --label-language en` |
| renommer un thème à la main | modifier `label` dans `output/themes.json`, puis relancer |
| écarter une collection de sources | ajouter `--exclude-collection "nom de la collection"` |
| avoir moins de thèmes | ajouter `--themes 5` |
| avoir des sous-thèmes plus fins | ajouter `--subthemes 60` |
| repartir de zéro | ajouter `--refit` |
| afficher mon nom sur la page | ajouter `--name "Bibliothèque Zotero de Camille Martin"` |
| analyser une bibliothèque de groupe | `uv run zotero-archive libraries`, puis ajouter `--library "nom" --out output-nom` |
| publier la page | ajouter `--web ../mon-site/zotero-archive` |

Quelques points à connaître :

- **Les thèmes sont figés après le premier calcul.** Les références déjà
  classées gardent leur sous-thème, les nouvelles rejoignent le sous-thème le
  plus proche, et vos libellés restent valables. Une référence supprimée de
  Zotero disparaît de la page à la génération suivante.
- **Changer les thèmes réinitialise les libellés.** `--refit`, `--themes`,
  `--subthemes`, `--model`, `--library` et `--exclude-collection` recalculent
  les thèmes ; les libellés précédents sont sauvegardés dans `themes.json.bak`,
  et la commande le signale (*paramètres modifiés : les thèmes sont
  recalculés*).
- **Un dossier de sortie par bibliothèque.** Le cache appartient à une
  bibliothèque et à un jeu d'options. Pour analyser aussi une bibliothèque de
  groupe, donnez-lui son propre dossier avec `--out`.
- **`--exclude-collection`** écarte toute référence rangée dans une collection
  dont le chemin contient le texte, sans tenir compte de la casse. Le chemin
  inclut les collections parentes, comme dans `Thèse / Sources / Presse`.
  L'option peut être répétée.

### Publier la page sur le web

La page de `output/` est pour vous : ses liens ouvrent votre propre Zotero, et
elle contient vos clés d'items et vos noms de collections. Pour publier,
demandez une seconde page, distincte :

```sh
uv run zotero-archive build --name "Bibliothèque Zotero de Camille Martin" --web ../mon-site/zotero-archive
```

La commande écrit `index.html` dans le dossier indiqué. Par défaut, cette page
contient **les graphiques seuls** : thèmes, sous-thèmes, leurs noms et leurs
mots caractéristiques, et la date et le sous-thème de chaque ajout. Elle ne
contient ni titre, ni auteur, ni clé Zotero, ni lien vers Zotero, ni tag, ni nom
de collection. Gardez à l'esprit que les noms et les mots caractéristiques sont
tirés des titres et des résumés de vos références.

Ajoutez `--web-references` pour publier aussi la liste des références (titre,
premiers auteurs, année, type, date d'ajout). Les liens se limitent alors aux
DOI : les adresses enregistrées par Zotero ne sont jamais publiées, car
certaines mènent à des webmails, des intranets ou des documents partagés.
Relisez la liste avant de la publier : une bibliothèque contient souvent des
documents internes ou inédits dont vous ne voulez pas forcément voir le titre
en ligne.

Le fichier est statique et sans dépendance externe : n'importe quel hébergement
convient. Avec **GitHub Pages**, placez le dossier dans le dépôt de votre site,
puis faites un commit et un push :

```sh
cd ../mon-site
git add zotero-archive
git commit -m "Ajoute la page Zotero comme archive"
git push
```

La page est alors servie à l'adresse `https://<votre-site>/zotero-archive/`.
Sur un site Jekyll, le fichier est copié tel quel, puisqu'il n'a pas d'en-tête
YAML. Si vous n'avez pas encore de site, voyez la
[documentation de GitHub](https://docs.github.com/fr/pages). Pour mettre à jour
la page publiée, relancez la même commande, puis commit et push.

### Référence des commandes

Il y a deux commandes. Toutes deux acceptent `--db CHEMIN`, l'emplacement de
`zotero.sqlite` s'il n'est pas dans `~/Zotero`.

**`uv run zotero-archive libraries`** liste les bibliothèques de la base : un
identifiant, le nombre de références et le nom. Votre bibliothèque personnelle
vient en premier, puis les bibliothèques de groupe.

**`uv run zotero-archive build`** analyse une bibliothèque et écrit la page. Ses
options :

| Option | Effet | Défaut |
| --- | --- | --- |
| **Ce qui est analysé** | | |
| `--library NOM` | une bibliothèque de groupe, par son nom, une partie de son nom ou son identifiant | bibliothèque personnelle |
| `--exclude-collection TEXTE` | écarter les références des collections dont le chemin contient TEXTE (répétable) | aucune |
| **Thèmes** | | |
| `--themes N` | nombre de thèmes, de 2 à 8 | 8 |
| `--subthemes N` | nombre de sous-thèmes ; jamais plus d'un pour 30 références | 40 |
| `--model NOM` | le modèle [sentence-transformers](https://www.sbert.net/) qui représente les références | `paraphrase-multilingual-mpnet-base-v2` |
| `--refit` | recalculer les thèmes au lieu de reprendre les précédents | non |
| **Noms** | | |
| `--label-model MODÈLE` | faire nommer les thèmes par un modèle servi par Ollama, par exemple `qwen3:8b` | mots caractéristiques |
| `--label-language LANGUE` | avec `--label-model` : langue des noms, par son code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) ou son nom | `fr` |
| `--ollama-url URL` | adresse d'Ollama ; si elle désigne une autre machine, les descriptions de vos thèmes y sont envoyées | `http://localhost:11434` |
| **Page** | | |
| `--name TEXTE` | nom affiché pour la bibliothèque | *Ma bibliothèque*, ou le nom du groupe |
| `--bulk-threshold N` | nombre d'ajouts à partir duquel un jour compte comme import en masse | 100 |
| `--open` | ouvrir la page dans le navigateur | non |
| **Sortie** | | |
| `--out DOSSIER` | dossier de sortie | `output` |
| `--web DOSSIER` | écrire aussi dans DOSSIER une page destinée à la publication | aucune |
| `--web-references` | avec `--web` : publier aussi la liste des références | non |

Ce que coûte chaque type de changement :

| Vous changez… | Vecteurs | Thèmes | Libellés |
| --- | --- | --- | --- |
| rien ; des références ont été ajoutées dans Zotero | calculés pour les nouvelles | conservés ; les nouvelles références rejoignent le sous-thème le plus proche | conservés |
| `--label-model`, `--label-language` | conservés | conservés | les noms du modèle sont refaits ; les vôtres sont conservés |
| `--name`, `--bulk-threshold`, `--web`, `--open` | conservés | conservés | conservés |
| `--themes`, `--subthemes`, `--exclude-collection`, `--refit` | conservés | recalculés | réinitialisés, avec sauvegarde |
| `--model`, `--library` | recalculés | recalculés | réinitialisés, avec sauvegarde |

### Comment ça marche

1. **Extraction** (`extract.py`). La base est copiée dans un dossier temporaire
   et la copie est ouverte en lecture seule, ce qui fonctionne aussi pendant que
   Zotero tourne. Tout item qui n'est ni une note, ni une pièce jointe, ni une
   annotation, qui n'est pas dans la corbeille et qui a un titre est retenu,
   avec son titre, son résumé, sa date d'ajout, son type, ses auteurs, son année
   de publication, son DOI, ses tags et ses collections.
2. **Représentation** (`embed.py`). Le titre et le résumé sont transformés en
   vecteur par un modèle multilingue
   ([paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2)),
   de sorte que « histoire économique » et « economic history » soient voisins.
   Ce modèle lit environ les cent premiers mots : le titre et le début du
   résumé. Les vecteurs sont mis en cache : seules les références nouvelles ou
   modifiées sont recalculées.
3. **Sous-thèmes** (`themes.py`). UMAP réduit les vecteurs à cinq dimensions,
   et k-means découpe cet espace en sous-thèmes.
4. **Thèmes**. Les sous-thèmes sont fusionnés deux à deux, selon le critère de
   Ward, jusqu'à ce qu'il reste le nombre de thèmes demandé. Le critère tient
   compte des tailles : les petits sous-thèmes sont absorbés d'abord, ce qui
   garde des thèmes de poids comparable.
5. **Ordre**. Les thèmes sont numérotés selon la date médiane d'ajout de leurs
   références, et de même les sous-thèmes à l'intérieur de chaque thème. C'est
   ce qui ordonne la légende et attribue les couleurs.
6. **Description**. Pour chaque groupe, un TF-IDF par classe retient les mots
   et expressions de deux mots fréquents dans le groupe et rares ailleurs, après
   avoir retiré les mots-outils de sept langues et fusionné les variantes d'un
   même mot d'une langue à l'autre (« europe », « european », « européenne »).
   Les références typiques sont les cinq plus proches du centre du groupe.
7. **Noms** (`labels.py`, en option). Un modèle servi par Ollama nomme chaque
   groupe à partir de cette description.
8. **Page** (`template.html`). Les données sont insérées dans un seul fichier
   HTML, qui calcule les graphiques dans le navigateur.

Les étapes aléatoires utilisent une graine fixe : sur la même machine, la même
bibliothèque et les mêmes options donnent les mêmes thèmes. Les dates sont
celles qu'enregistre Zotero, en temps universel.

### Ce qui reste privé

| | `output/index.html` | page `--web` | `--web` avec `--web-references` |
| --- | --- | --- | --- |
| noms et mots caractéristiques des thèmes | oui | oui | oui |
| date et sous-thème de chaque ajout | oui | oui | oui |
| titres, auteurs, année, type | oui | non | oui |
| liens | vers votre Zotero | aucun | DOI seulement |
| clés Zotero, noms de collections | oui | non | non |
| résumés, tags, adresses, pièces jointes | non | non | non |

`themes.json` et `.cache/` restent sur votre ordinateur et ne font jamais partie
d'une page publiée. Les seules connexions au réseau sont l'installation, le
téléchargement des modèles et, si vous l'utilisez, l'adresse donnée avec
`--ollama-url`.

### En cas de problème

| Message ou symptôme | Signification | Que faire |
| --- | --- | --- |
| *Base Zotero introuvable* | `zotero.sqlite` n'est pas dans `~/Zotero` | indiquer son emplacement avec `--db` (voir [Installer](#installer)) |
| *Il faut au moins 60 références pour dégager des thèmes* | la bibliothèque, ou ce qu'il en reste après `--exclude-collection`, est trop petite | analyser une bibliothèque plus fournie, ou écarter moins |
| *Bibliothèque « … » introuvable ou ambiguë* | aucune bibliothèque, ou plusieurs, ne correspondent à `--library` | lancer `zotero-archive libraries` et reprendre le nom exact ou l'identifiant |
| *Ollama ne répond pas à l’adresse …* | Ollama n'est pas lancé | lancer l'application Ollama, ou `ollama serve` |
| *Le modèle « … » n’est pas installé dans Ollama* | le modèle n'a jamais été téléchargé | `ollama pull <modèle>` ; le message liste ceux qui sont installés |
| *paramètres modifiés : les thèmes sont recalculés* | une option qui définit les thèmes a changé | rien ; vos libellés précédents sont dans `themes.json.bak` |
| *--label-language s’emploie avec --label-model* | une langue a été donnée sans modèle | ajouter `--label-model` |
| la première exécution semble bloquée | le modèle (1 Go) est en cours de téléchargement | patienter ; les exécutions suivantes n'utilisent pas le réseau |
| un titre n'ouvre pas Zotero | les liens `zotero://` demandent l'application Zotero sur le même ordinateur | ouvrir la page sur l'ordinateur où Zotero est installé |
| les thèmes ne conviennent pas | le nombre de thèmes ne correspond pas à la bibliothèque, ou un corpus la domine | essayer `--themes`, `--subthemes` ou `--exclude-collection` |

Pour tout retirer : supprimez le dossier cloné, qui contient l'environnement
Python et `output/`, ainsi que le modèle, dans
`~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-mpnet-base-v2`.

### Réutiliser et adapter le code

Le code est court et chaque fichier a un seul rôle.

| Fichier | Rôle | Points d'entrée |
| --- | --- | --- |
| `src/zotero_archive/extract.py` | lire une base Zotero | `open_snapshot`, `list_libraries`, `find_library`, `load_items`, la classe `Item` |
| `src/zotero_archive/embed.py` | transformer des textes en vecteurs, avec un cache | `embed_texts` |
| `src/zotero_archive/themes.py` | regrouper en thèmes et les décrire | `fit`, `assign`, `describe` |
| `src/zotero_archive/labels.py` | nommer les groupes avec Ollama | `check`, `describe`, `propose` |
| `src/zotero_archive/pipeline.py` | enchaîner les étapes et écrire les fichiers | `Options`, `run` |
| `src/zotero_archive/cli.py` | la ligne de commande | `main` |
| `src/zotero_archive/template.html` | la page : structure, styles et script dans un seul fichier | |
| `tests/` | les tests | `uv run pytest` |

**Où changer quoi.**

| Pour changer… | Voir |
| --- | --- |
| les textes de la page, ou la traduire | `template.html` |
| les couleurs | les variables `--s1` à `--s8`, en tête de `template.html` |
| les consignes données au modèle qui nomme | `SYSTEM_FR` et `SYSTEM_OTHER` dans `labels.py` |
| les langues dont les mots-outils sont ignorés | `STOPWORD_LANGUAGES` et `EXTRA_STOPWORDS` dans `themes.py` |
| les noms des types de documents affichés dans la page | `TYPE_LABELS` dans `pipeline.py` |
| le modèle par défaut, ou la quantité de texte qu'il reçoit | `DEFAULT_MODEL` et `MAX_CHARS` dans `embed.py` |
| les items Zotero qui comptent comme références | `NON_REFERENCE_TYPES` dans `extract.py` |

**Utiliser les briques dans votre propre script.** L'extraction est utile seule,
par exemple dans un carnet. Ceci compte les références ajoutées chaque année :

```python
from collections import Counter

from zotero_archive.extract import DEFAULT_DB, find_library, load_items, open_snapshot

with open_snapshot(DEFAULT_DB) as con:
    library = find_library(con, None)  # None : votre bibliothèque personnelle
    items = load_items(con, library)

per_year = Counter(item.date_added[:4] for item in items)
for year, n in sorted(per_year.items()):
    print(year, n)
```

Chaque item a les champs `key`, `item_type`, `date_added`, `title`, `abstract`,
`year`, `language`, `doi`, `creators`, `tags` et `collections`. Toute la chaîne
peut aussi se lancer depuis Python, avec les mêmes options que la ligne de
commande :

```python
from pathlib import Path

from zotero_archive.pipeline import Options, run

page = run(Options(out=Path("output-test"), n_themes=6, name="Ma bibliothèque"))
```

Enregistrez un script dans le dossier du projet et lancez-le avec
`uv run python mon_script.py`.

**Tests.** `uv run pytest` les exécute en quelques secondes. Ils utilisent une
base Zotero miniature et un substitut d'Ollama : ils n'ont besoin ni de votre
bibliothèque ni d'un modèle.

### Limites

- La date d'ajout d'une référence n'est pas celle de sa lecture, et un import en
  masse donne une date unique à des références accumulées sur des années.
- Seuls les titres et les résumés sont analysés. Une référence sans résumé est
  classée d'après son seul titre.
- Chaque référence appartient à un seul thème, alors qu'un texte peut relever de
  plusieurs.
- Le découpage dépend du nombre de thèmes demandé et du modèle. C'est une
  proposition de lecture, à confronter à ce que vous savez de votre
  bibliothèque, pas un résultat.
- Huit thèmes au maximum : au-delà, les couleurs ne se distinguent plus de façon
  fiable. Le détail passe par les sous-thèmes.
- Les noms proposés par un modèle de langue sont eux aussi des suggestions. Un
  petit modèle se trompe parfois sur un groupe, peut donner le même nom à deux
  groupes, et écrit mieux les langues les plus répandues que les autres.
- La page et les messages de la commande sont en français uniquement.

### Licence

[GNU General Public License v3.0 ou ultérieure](LICENSE).
