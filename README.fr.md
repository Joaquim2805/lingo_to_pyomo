# LingoPy

[🇬🇧 English](README.md)

![Tests](https://github.com/Joaquim2805/lingo_to_pyomo/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

LingoPy convertit des modèles d’optimisation LINGO (`.lng`) en code source Pyomo et en notebooks Jupyter. Il peut être utilisé de deux façons :

- depuis l’interface web Flask, pour convertir un ou plusieurs fichiers sans écrire de code ;
- depuis Python, pour appeler séparément le parser, le générateur Pyomo, le nettoyage, la conversion Excel `@OLE` et la génération de notebooks.

Les deux modes utilisent le même pipeline : le fichier LINGO est analysé, transformé en modèle intermédiaire, puis converti en code Pyomo. Le code généré peut ensuite être enregistré ou intégré dans un notebook.

## Fonctionnement

Le pipeline de conversion est le suivant :

1. Lecture du fichier LINGO avec la grammaire Lark de `src/lingo_parser/lingogem.lark`.
2. Transformation de l’arbre syntaxique en dictionnaire Python contenant les ensembles, données, contraintes, boucles et l’objectif.
3. Génération d’un modèle Pyomo sous forme de code Python.
4. Export facultatif des données du modèle au format JSON ou DAT Pyomo/AMPL.
5. Création facultative d’un notebook Jupyter contenant le code généré, le chargement des données, la résolution et l’affichage des résultats.

Les modèles contenant `@OLE` peuvent d’abord être convertis depuis des zones nommées Excel vers des données LINGO explicites.

## Installation

Le dépôt n’est pas distribué comme paquet Python installable. Les commandes doivent être lancées depuis la racine du dépôt et `src` doit rester importable, comme dans l’exemple Python ci-dessous.

Python 3.10 ou une version ultérieure est nécessaire à cause de la syntaxe d’annotations utilisée par le code source. Installez les dépendances dans un environnement virtuel :

```bash
git clone https://github.com/Joaquim2805/lingo_to_pyomo.git
cd lingo_to_pyomo
python -m venv .venv
```

Activez l’environnement :

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows cmd.exe
.venv\Scripts\activate.bat
```

Installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

Les modèles générés nécessitent un solveur Pyomo disponible. Les tests utilisent HiGHS (`highs`). Gurobi, CPLEX et GLPK peuvent également être sélectionnés dans l’interface si leur installation locale et, le cas échéant, leur licence sont disponibles.

## Interface web

Depuis la racine du dépôt, lancez l’application Flask :

```bash
python dev/app.py
```

Ouvrez ensuite <http://127.0.0.1:5000>.

L’interface accepte un modèle sélectionné dans `data/` ou un fichier `.lng` importé. Elle permet :

- de convertir directement un modèle en code Pyomo et en notebook ;
- de nettoyer un fichier LINGO et d’enregistrer une version `_clean.lng` ;
- de convertir les références `@OLE` avec un classeur Excel importé en option ;
- d’exécuter le pipeline complet : conversion OLE facultative, nettoyage facultatif, parsing, génération Pyomo, export JSON/DAT facultatif et génération du notebook ;
- de traiter plusieurs modèles par lots et de regrouper les fichiers produits dans une archive ZIP.

Les notebooks produits sont placés dans `notebooks/`, les fichiers de données dans `data/`, et les fichiers importés ou associés aux tâches sous `dev/uploads/`. L’interface accepte les noms de solveur HiGHS, Gurobi, CPLEX et GLPK ; elle n’installe pas ces solveurs et ne vérifie pas leur présence.

## Bibliothèque Python

LingoPy s’utilise directement depuis le dépôt et n’est pas installé comme paquet Python. Ajoutez `src` à `sys.path`, puis utilisez les fonctions suivantes :

- `parse_lingo_model(path)` analyse un fichier LINGO et renvoie son arbre syntaxique. `LingoModelTransformer2().transform(tree)` convertit ensuite cet arbre en représentation Python du modèle.
- `generate_pyomo_code(model_dict, external_data=False, data_filename=..., external_data_format=...)` renvoie le code source Pyomo.
- `save_pyomo_data_to_json(...)` et `save_pyomo_data_to_dat(...)` exportent les données externes. `load_pyomo_data(...)` lit les données JSON.
- `generate_pyomo_notebook(...)` écrit un notebook Jupyter à partir du code Pyomo généré.
- `clean_lingo_file(...)` et `clean_lingo_content(...)` nettoient l’entrée LINGO. `convert_lingo_ole_to_explicit(...)` remplace les données Excel `@OLE` par des valeurs explicites.

### Exemple de conversion

Cet exemple utilise le modèle fourni `data/California.lng` et produit une chaîne de code Pyomo ainsi qu’un notebook :

```python
import sys

sys.path.insert(0, "src")

from lingo_parser.parser import parse_lingo_model
from lingo_parser.transformer import LingoModelTransformer2
from notebook_generator.notebook_construct import generate_pyomo_notebook
from pyomo_generator.json_parser import generate_pyomo_code

input_path = "data/California.lng"
tree = parse_lingo_model(input_path)
model_dict = LingoModelTransformer2().transform(tree)

pyomo_code = generate_pyomo_code(model_dict)
print(pyomo_code)

generate_pyomo_notebook(
    pyomo_code,
    solver="highs",
    filename="notebooks/California_from_api.ipynb",
)
```

Avec `external_data=True`, exportez d’abord les données puis transmettez le même format et le même chemin au générateur :

```python
from pyomo_generator.json_parser import save_pyomo_data_to_json

data_path = save_pyomo_data_to_json(model_dict, "data/California_data.json")
pyomo_code = generate_pyomo_code(
    model_dict,
    external_data=True,
    data_filename=data_path,
    external_data_format="json",
)
```

Pour produire un fichier DAT, utilisez `save_pyomo_data_to_dat` et `external_data_format="dat"`. Les modèles DAT sont générés sous forme de `AbstractModel` Pyomo puis chargés avec `create_instance`; les données JSON sont chargées par l’aide générée.

## Syntaxe LINGO prise en charge

La grammaire active et le transformateur couvrent notamment :

- `MODEL:`, `SETS: ... ENDSETS`, `DATA: ... ENDDATA` et `END` ;
- les objectifs `MAX` et `MIN` ;
- les ensembles nommés, leurs éléments, les intervalles numériques ou nommés, et les ensembles indexés/cartésiens ;
- les références scalaires, unidimensionnelles et multidimensionnelles ;
- les opérateurs `+`, `-`, `*`, `/`, les parenthèses et les comparaisons `<=`, `>=`, `=` ;
- `@SUM`, y compris les expressions indexées et les filtres conditionnels ;
- `@FOR`, y compris les boucles imbriquées et les filtres `#GE#`, `#LE#`, `#GT#`, `#LT#`, `#EQ#`, `#NE#`, `#AND#` et `#OR#` ;
- `@BIN` pour l’inférence des variables binaires et `@GIN` pour l’inférence du domaine entier ;
- la syntaxe `@OLE` utilisée par le chemin de conversion Excel.

`@ODBC` est reconnu par la grammaire, mais aucun chargement ODBC n’est implémenté. Lorsqu’une fonction ou une expression LINGO n’est pas reconnue, LingoPy le signale dans le code Pyomo généré avec un commentaire `TODO`. Le résultat doit alors être vérifié et complété manuellement.

## Limitations

- Les fonctions LINGO non reconnues sont signalées par des commentaires `TODO` dans le code Pyomo généré ; elles ne sont pas converties automatiquement.
- Un notebook généré nécessite Jupyter, Pyomo et le solveur choisi installés localement.
- La conversion `@OLE` est limitée aux zones nommées Excel. Le nettoyeur modifie aussi le texte d’entrée : vérifiez le fichier nettoyé avant de l’utiliser.

## Structure du dépôt

```text
lingo_to_pyomo/
├── src/
│   ├── lingo_parser/           # Grammaire Lark, parser, transformateur, nettoyeur
│   ├── pyomo_generator/        # Génération Pyomo et export JSON/DAT
│   ├── notebook_generator/     # Génération de notebooks Jupyter
│   ├── excel_parser/           # Zones nommées Excel et conversion @OLE
│   └── test/                   # Tests pytest
├── dev/
│   ├── app.py                  # Point d’entrée Flask
│   ├── blueprints/             # Routes web, traitement par lots et API
│   ├── services/               # Services de conversion et de gestion des fichiers
│   └── templates/              # Templates Flask
├── data/                       # Exemples LINGO et fichiers de données
├── notebooks/                  # Notebooks générés et conservés dans le dépôt
├── docs/                       # Point d’entrée MkDocs et génération de l’API
├── requirements.txt
└── README.md
```

## Tests, notebooks et documentation

Depuis la racine du dépôt, lancez les tests :

```bash
pytest src/test/ -v
```

Les tests couvrent la génération de modèles et leur résolution avec HiGHS, les données externes JSON/DAT, la conversion Excel/OLE et le nettoyage LINGO. Les tests Excel écrivent des fichiers de comparaison dans `data/`.

Les notebooks de `notebooks/` sont des exemples ou des fichiers d’expérimentation générés ; ils ne sont pas nécessaires à l’utilisation normale. De nouveaux notebooks peuvent être produits depuis l’interface web, l’API Python ou le pipeline.

Pour servir la documentation MkDocs :

```bash
mkdocs serve
```

Ouvrez ensuite <http://127.0.0.1:8000>. La référence API est générée à partir des docstrings du code source par la configuration MkDocs.

## Auteurs

Fausto Errico, Virginie Destuynder et Joaquim Jusseau.
