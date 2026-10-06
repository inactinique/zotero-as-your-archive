# Zotero as your archive · Zotero comme archive

[English](#english) · [Français](#français)

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

> The generated page and the command-line messages are in French for now. The
> names of the themes can be requested in another language (step 5).

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
  have the themes named by a local language model (step 5). Allow a few more
  gigabytes for that model.

Developed and tested on macOS (Apple Silicon) with Zotero 10. Nothing in the
code is specific to macOS, but Linux and Windows have not been tested.

### Step by step

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

**3. Check where Zotero keeps its data.** By default it is the `Zotero` folder
in your home directory (`~/Zotero`, or `C:\Users\<you>\Zotero` on Windows),
which contains a file named `zotero.sqlite`. If you moved it, the location is
shown in Zotero under *Settings → Advanced → Files and Folders → Data Directory
Location*; pass it with `--db /path/to/zotero.sqlite` in the commands below.

**4. Build the page.**

```sh
uv run zotero-archive build --open
```

On first use, uv downloads Python 3.12 and the dependencies. The first build
then downloads the language model (about 1 GB) and computes a representation of
every reference: for 7,400 references on a recent laptop, the computation took
about a minute and a half, on top of the download. Later builds only process
new references and take about a second. Zotero can stay open in the meantime.

The `output/` folder then contains:

- `index.html`: the page, a single self-contained file that opens in a browser;
- `themes.json`: the description of the themes, where you can rename them.

`output/` is ignored by git, because these files contain your library.

**5. Name the themes.** The automatic labels are the three words that best
distinguish each group, and they are often rough. There are two ways to improve
them, and they combine.

*Let a local language model propose names.* If [Ollama](https://ollama.com) is
running on your computer, add `--label-model` with the name of a model you have
pulled:

```sh
uv run zotero-archive build --label-model qwen3:8b
```

For each theme and sub-theme, the model is given the distinctive words, the
Zotero collections most present and a few typical titles, and answers with a
short name. It runs on your machine, so your library still does not leave it.
With `qwen3:8b` (5 GB) on a recent laptop, naming 48 groups took about a minute.

The names are in French by default. For another language, add
`--label-language` with a code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) or the
name of any other language:

```sh
uv run zotero-archive build --label-model qwen3:8b --label-language en
```

The names are stored in `themes.json` and reused by later builds: you only need
these options again after recomputing the themes, to try another model, or to
change language. Read the proposals: a small model is right most of the time,
not always.

*Rename by hand.* Open `output/themes.json`: for each theme and sub-theme it
lists the distinctive words, the Zotero collections most present in it and a few
typical references. Edit the `label` fields, then run the build command again.
A label you wrote is never replaced by the model's.

**6. Adjust if needed.** Useful options are `--themes` (2 to 8),
`--subthemes`, and `--exclude-collection TEXT` to leave out a collection that
is a corpus of sources rather than reading (see [Options](#options)). Changing
one of these recomputes the themes and resets your labels; the previous file is
kept as `themes.json.bak`.

**7. Come back later.** Run the same command whenever you like. The themes are
frozen after the first computation: references already classified keep their
sub-theme, new ones join the nearest sub-theme, and your labels stay valid. Use
`--refit` to recompute everything.

To analyse a group library instead of your personal one, list the libraries
with `uv run zotero-archive libraries`, then add `--library NAME`.

### Reading the page

1. **What enters the library, period by period.** One column per year (or
   half-year, or quarter), split by theme. As a *share of additions*, all
   columns have the same height and grey bars above recall the actual volume;
   as a *number of references*, the column height is that volume.
2. **Trajectory of each theme.** One row per theme, from the oldest to the most
   recent, with its peak. Click a theme to unfold its sub-themes.
3. **References.** Click a theme, a bar or a curve to list the matching
   references; each title opens the reference in Zotero.

A checkbox sets aside *bulk imports*: days when many references arrived at once
(an old database, a press corpus), which otherwise flatten the rest of the
period.

### Publishing the page on the web

The page in `output/` is for you: its links open your own Zotero, and it
contains your item keys and collection names. To publish, ask for a second,
separate page:

```sh
uv run zotero-archive build --name "Zotero library of Jane Doe" --web ../my-site/zotero-archive
```

This writes `index.html` into the folder you name. By default that page
contains **the charts only**: themes, sub-themes, their distinctive words, and
the date and sub-theme of each addition. It contains no title, author, Zotero
key, link to Zotero, tag or collection name. Bear in mind that the distinctive
words are drawn from the titles and abstracts of your references.

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

### Options

| Option of `build` | Effect |
| --- | --- |
| `--db PATH` | location of `zotero.sqlite`, if it is not in `~/Zotero` |
| `--library NAME` | analyse a group library (`zotero-archive libraries` lists them) |
| `--out FOLDER` | output folder (default: `output`) |
| `--themes N` | number of themes, from 2 to 8 (default: 8) |
| `--subthemes N` | number of sub-themes (default: 40; fewer for small libraries) |
| `--exclude-collection TEXT` | leave out references filed in a collection whose path contains TEXT (repeatable) |
| `--bulk-threshold N` | number of additions from which a day counts as a bulk import (default: 100) |
| `--model NAME` | another [sentence-transformers](https://www.sbert.net/) model |
| `--refit` | recompute the themes instead of reusing the previous ones |
| `--label-model MODEL` | have the themes named by a language model served by Ollama, e.g. `qwen3:8b` |
| `--label-language LANG` | with `--label-model`: language of the proposed names, as a code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) or a language name (default: `fr`) |
| `--ollama-url URL` | address of Ollama (default: `http://localhost:11434`); if you point it at another machine, the descriptions of your themes are sent there |
| `--name TEXT` | name displayed for the library |
| `--web FOLDER` | also write a page for publication into FOLDER |
| `--web-references` | with `--web`: publish the list of references too |
| `--open` | open the page in the browser |

### How it works

1. **Extraction** (`extract.py`): title, abstract, date added, type, authors,
   tags and collections of each reference, leaving out notes, attachments and
   the trash.
2. **Representation** (`embed.py`): title and abstract are turned into a vector
   by a multilingual model
   ([paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2)),
   so that "histoire économique" and "economic history" end up close together.
3. **Themes** (`themes.py`): UMAP reduces the vectors to five dimensions,
   k-means cuts sub-themes in that space, and Ward's criterion merges them into
   themes. The distinctive words come from a TF-IDF computed per group. Themes
   are numbered by the median date at which their references were added.
4. **Names** (`labels.py`, optional): a language model served by Ollama names
   each group from its distinctive words and a few typical titles.
5. **Page** (`template.html`): the data are embedded in one HTML file.

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

### Development

```sh
uv run pytest
```

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
  faire nommer les thèmes par un modèle de langue local (étape 5). Prévoyez
  quelques gigaoctets de plus pour ce modèle.

Développé et testé sous macOS (Apple Silicon) avec Zotero 10. Rien dans le code
n'est propre à macOS, mais Linux et Windows n'ont pas été testés.

### Pas à pas

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

**3. Vérifiez où Zotero range ses données.** Par défaut, c'est le dossier
`Zotero` de votre répertoire personnel (`~/Zotero`, ou `C:\Users\<vous>\Zotero`
sous Windows), qui contient un fichier `zotero.sqlite`. Si vous l'avez déplacé,
son emplacement est indiqué dans Zotero, sous *Paramètres → Avancées → Fichiers
et dossiers → Emplacement du répertoire de données* ; indiquez-le avec
`--db /chemin/vers/zotero.sqlite` dans les commandes ci-dessous.

**4. Générez la page.**

```sh
uv run zotero-archive build --open
```

À la première utilisation, uv télécharge Python 3.12 et les dépendances. La
première génération télécharge ensuite le modèle de langue (environ 1 Go) et
calcule une représentation de chaque référence : pour 7 400 références sur un
portable récent, le calcul a pris environ une minute et demie, en plus du
téléchargement. Les générations suivantes ne traitent que les nouvelles
références et durent environ une seconde. Zotero peut rester ouvert pendant ce
temps.

Le dossier `output/` contient alors :

- `index.html` : la page, un fichier autonome qui s'ouvre dans un navigateur ;
- `themes.json` : la description des thèmes, où vous pouvez les renommer.

`output/` est ignoré par git, car ces fichiers contiennent votre bibliothèque.

**5. Nommez les thèmes.** Les libellés automatiques sont les trois mots qui
distinguent le mieux chaque groupe, et ils sont souvent approximatifs. Il y a
deux façons de les améliorer, qui se combinent.

*Laisser un modèle de langue local proposer des noms.* Si
[Ollama](https://ollama.com) tourne sur votre ordinateur, ajoutez
`--label-model` suivi du nom d'un modèle que vous avez installé :

```sh
uv run zotero-archive build --label-model qwen3:8b
```

Pour chaque thème et sous-thème, le modèle reçoit les mots caractéristiques, les
collections Zotero les plus présentes et quelques titres typiques, et répond par
un nom court. Il s'exécute sur votre machine : votre bibliothèque ne la quitte
toujours pas. Avec `qwen3:8b` (5 Go) sur un portable récent, nommer 48 groupes a
pris environ une minute.

Les noms sont en français par défaut. Pour une autre langue, ajoutez
`--label-language` suivi d'un code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) ou
du nom de n'importe quelle autre langue :

```sh
uv run zotero-archive build --label-model qwen3:8b --label-language en
```

Les noms sont enregistrés dans `themes.json` et repris par les générations
suivantes : ces options ne redeviennent nécessaires qu'après un recalcul des
thèmes, pour essayer un autre modèle ou pour changer de langue. Relisez les
propositions : un petit modèle a raison la plupart du temps, pas toujours.

*Renommer à la main.* Ouvrez `output/themes.json` : pour chaque thème et
sous-thème, il donne les mots caractéristiques, les collections Zotero les plus
présentes et quelques références typiques. Modifiez les champs `label`, puis
relancez la commande. Un libellé que vous avez écrit n'est jamais remplacé par
celui du modèle.

**6. Ajustez si nécessaire.** Les options utiles sont `--themes` (de 2 à 8),
`--subthemes`, et `--exclude-collection TEXTE` pour écarter une collection qui
est un corpus de sources plutôt qu'une lecture (voir [Options](#options-1)).
Modifier l'une d'elles recalcule les thèmes et réinitialise vos libellés ;
l'ancien fichier est conservé sous le nom `themes.json.bak`.

**7. Revenez-y plus tard.** Relancez la même commande quand vous voulez. Les
thèmes sont figés après le premier calcul : les références déjà classées gardent
leur sous-thème, les nouvelles rejoignent le sous-thème le plus proche, et vos
libellés restent valables. L'option `--refit` recalcule tout.

Pour analyser une bibliothèque de groupe plutôt que votre bibliothèque
personnelle, listez les bibliothèques avec `uv run zotero-archive libraries`,
puis ajoutez `--library NOM`.

### Lire la page

1. **Ce qui entre dans la bibliothèque, période par période.** Une colonne par
   année (ou semestre, ou trimestre), découpée selon les thèmes. En *part des
   ajouts*, toutes les colonnes ont la même hauteur et des barres grises, au-dessus,
   rappellent le volume réel ; en *nombre de références*, la hauteur de la
   colonne donne ce volume.
2. **Trajectoire de chaque thème.** Une ligne par thème, du plus ancien au plus
   récent, avec son maximum. Un clic sur un thème déplie ses sous-thèmes.
3. **Références.** Un clic sur un thème, une barre ou une courbe affiche les
   références concernées ; chaque titre ouvre la référence dans Zotero.

Une case à cocher écarte les *imports en masse* : les jours où beaucoup de
références sont arrivées d'un coup (une ancienne base, un corpus de presse), qui
écrasent sinon le reste de la période.

### Publier la page sur le web

La page de `output/` est pour vous : ses liens ouvrent votre propre Zotero, et
elle contient vos clés d'items et vos noms de collections. Pour publier,
demandez une seconde page, distincte :

```sh
uv run zotero-archive build --name "Bibliothèque Zotero de Camille Martin" --web ../mon-site/zotero-archive
```

La commande écrit `index.html` dans le dossier indiqué. Par défaut, cette page
contient **les graphiques seuls** : thèmes, sous-thèmes, leurs mots
caractéristiques, et la date et le sous-thème de chaque ajout. Elle ne contient
ni titre, ni auteur, ni clé Zotero, ni lien vers Zotero, ni tag, ni nom de
collection. Gardez à l'esprit que les mots caractéristiques sont tirés des
titres et des résumés de vos références.

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

### Options

| Option de `build` | Effet |
| --- | --- |
| `--db CHEMIN` | emplacement de `zotero.sqlite`, s'il n'est pas dans `~/Zotero` |
| `--library NOM` | analyser une bibliothèque de groupe (`zotero-archive libraries` les liste) |
| `--out DOSSIER` | dossier de sortie (défaut : `output`) |
| `--themes N` | nombre de thèmes, de 2 à 8 (défaut : 8) |
| `--subthemes N` | nombre de sous-thèmes (défaut : 40 ; moins pour une petite bibliothèque) |
| `--exclude-collection TEXTE` | écarter les références rangées dans une collection dont le chemin contient TEXTE (répétable) |
| `--bulk-threshold N` | nombre d'ajouts à partir duquel un jour compte comme import en masse (défaut : 100) |
| `--model NOM` | autre modèle [sentence-transformers](https://www.sbert.net/) |
| `--refit` | recalculer les thèmes au lieu de reprendre les précédents |
| `--label-model MODÈLE` | faire nommer les thèmes par un modèle de langue servi par Ollama, par exemple `qwen3:8b` |
| `--label-language LANGUE` | avec `--label-model` : langue des noms proposés, par son code (`fr`, `en`, `de`, `es`, `it`, `nl`, `pt`) ou son nom (défaut : `fr`) |
| `--ollama-url URL` | adresse d'Ollama (défaut : `http://localhost:11434`) ; si elle désigne une autre machine, les descriptions de vos thèmes y sont envoyées |
| `--name TEXTE` | nom affiché pour la bibliothèque |
| `--web DOSSIER` | écrire aussi dans DOSSIER une page destinée à la publication |
| `--web-references` | avec `--web` : publier aussi la liste des références |
| `--open` | ouvrir la page dans le navigateur |

### Méthode

1. **Extraction** (`extract.py`) : titre, résumé, date d'ajout, type, auteurs,
   tags et collections de chaque référence, hors notes, pièces jointes et
   corbeille.
2. **Représentation** (`embed.py`) : le titre et le résumé sont transformés en
   vecteur par un modèle multilingue
   ([paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2)),
   de sorte que « histoire économique » et « economic history » soient voisins.
3. **Thèmes** (`themes.py`) : UMAP réduit les vecteurs à cinq dimensions,
   k-means y découpe les sous-thèmes, puis le critère de Ward les fusionne en
   thèmes. Les mots caractéristiques viennent d'un TF-IDF calculé par groupe.
   Les thèmes sont numérotés selon la date médiane d'ajout de leurs références.
4. **Noms** (`labels.py`, en option) : un modèle de langue servi par Ollama
   nomme chaque groupe à partir de ses mots caractéristiques et de quelques
   titres typiques.
5. **Page** (`template.html`) : les données sont insérées dans un seul fichier
   HTML.

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

### Développement

```sh
uv run pytest
```

### Licence

[GNU General Public License v3.0 ou ultérieure](LICENSE).
