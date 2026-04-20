# LingPy — Documentation Technique

Bienvenue dans la documentation technique de **LingPy**, un convertisseur automatique de
modèles d'optimisation **LINGO → Pyomo**.

---

## À propos du projet

LingPy prend en entrée un fichier `.lng` (syntaxe LINGO) et produit automatiquement :

- un **script Python Pyomo** prêt à l'exécution,
- un **notebook Jupyter interactif** structuré par sections,
- optionnellement un **fichier de données externe** (JSON ou DAT) séparé du modèle.

Le projet est organisé en pipeline modulaire : chaque étape peut être utilisée
indépendamment ou enchaînée via l'interface Flask (`dev/`).

---

## Architecture du pipeline

```
Fichier .lng
     │
     ▼
┌─────────────────┐
│  lingo_cleaner  │  Nettoyage : accents, commentaires, casse uniforme
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  excel_module   │  Résolution @OLE : injection des données Excel dans le .lng
└────────┬────────┘
         │ (facultatif)
         ▼
┌─────────────────┐
│     parser      │  Parsing Lark → arbre syntaxique (parse tree)
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  LingoModelTransformer│  Transformation arbre → JSON structuré
└────────┬─────────────┘
         │
         ▼
┌─────────────────┐
│   json_parser   │  Génération du code Pyomo (sets, params, vars, contraintes)
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  notebook_construct  │  Emballage dans un notebook Jupyter (.ipynb)
└──────────────────────┘
```

---

## Modules

### `lingo_parser`

Gère toutes les étapes liées à la lecture et la normalisation des fichiers LINGO.

| Module          | Rôle                                                                                                                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `lingo_cleaner` | Nettoyage syntaxique : suppression des accents et commentaires, normalisation de la casse (ensembles en MAJUSCULE, paramètres en PascalCase) |
| `parser`        | Lecture du fichier `.lng` via Lark et production de l'arbre syntaxique                                                                       |
| `transformer`   | Parcours de l'arbre Lark et construction d'une représentation intermédiaire Python (dict)                                                    |

---

### `excel_parser`

Résout les références `@OLE(...)` présentes dans les fichiers LINGO qui stockent
leurs données dans des classeurs Excel.

| Module         | Rôle                                                                                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `excel_module` | Lit les **zones nommées** Excel (`openpyxl`), déduit les dimensions attendues des attributs LINGO et injecte les valeurs numériques directement dans le texte LINGO |

---

### `pyomo_generator`

Cœur de la conversion : prend le JSON produit par le Transformer et génère du code Pyomo.

| Module        | Rôle                                                                                                                       |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `json_parser` | Parse le JSON intermédiaire, traduit les @SUM/@FOR en compréhensions Pyomo, déclare Sets/Params/Vars/Constraints/Objective |

---

### `notebook_generator`

Empaquette le code Pyomo dans un notebook Jupyter lisible et exécutable.

| Module               | Rôle                                                                                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `notebook_construct` | Découpe le code Pyomo en sections, crée une cellule markdown + code par section, ajoute les cellules d'import, de chargement de données et d'affichage des résultats |

---

## Conventions de code

### Représentation intermédiaire (JSON)

Après parsing et transformation, le modèle LINGO est représenté comme un dictionnaire Python :

```python
{
    "sets": [
        {
            "name": "PRODUITS",
            "elements": ["P1", "P2", "P3"],
            "attrs": ["cout", "qte"]
        },
        {
            "name": "ARC",
            "indices": ["USINES", "CLIENTS"],
            "attrs": ["cap"]
        }
    ],
    "data": {
        "cout": [10.0, 20.0, 15.0],
        "cap":  [100.0, 200.0, ...]
    },
    "objective": "MAX = sum(cout(i) for i in PRODUITS)",
    "constraints": ["cout(i) <= 50", ...],
    "for_loops":   ["@FOR(PRODUITS(i): cout(i) <= 50)"],
}
```

### Style de docstrings

Toutes les fonctions utilisent le style **Google** (compatible `mkdocstrings`) :

```python
def ma_fonction(arg1: str, arg2: int = 0) -> dict:
    """Résumé sur une ligne.

    Description plus longue si nécessaire.

    Args:
        arg1: Description du premier argument.
        arg2: Description du deuxième argument (optionnel).

    Returns:
        Description du retour.

    Raises:
        ValueError: Si arg1 est vide.
    """
```

---

## Dépendances principales

| Paquet     | Rôle                                                 |
| ---------- | ---------------------------------------------------- |
| `lark`     | Parsing de la grammaire LINGO (fichier `.lark`)      |
| `pyomo`    | Bibliothèque d'optimisation cible                    |
| `nbformat` | Création des notebooks Jupyter                       |
| `openpyxl` | Lecture des fichiers Excel pour la résolution `@OLE` |
| `pandas`   | Manipulation des DataFrames lors de la lecture Excel |
| `flask`    | Interface web de conversion par lot                  |

---

## Référence API

Naviguez dans le menu **Référence API** pour consulter la documentation
auto-générée de chaque module depuis les docstrings du code source.
