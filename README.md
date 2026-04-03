# LINGO -> Pyomo

<div align="center">

![Tests](https://github.com/Joaquim2805/lingo_to_pyomo/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Convertisseur automatique de modeles LINGO vers notebooks Jupyter Pyomo

</div>

---

## Description

Projet pedagogique pour convertir des modeles d'optimisation LINGO (.lng) vers du code Pyomo et des notebooks Jupyter executables.

Le pipeline couvre:

- parsing LINGO (Lark)
- transformation AST -> dictionnaire Python
- generation du code Pyomo
- export notebook
- gestion des donnees externes en JSON ou DAT
- conversion des modeles `@OLE` en version explicite

---

## Installation

```bash
git clone https://github.com/Joaquim2805/lingo_to_pyomo.git
cd lingo_to_pyomo
python -m venv .venv
```

Activation de l'environnement virtuel:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Installation des dependances:

```bash
pip install -r requirements.txt
```

Prerequis:

- Python 3.8+
- un solveur d'optimisation (HiGHS, GLPK, Gurobi, CPLEX, IPOPT, ...)

---

## Lancer l'application Flask

Depuis la racine du projet:

```bash
python dev/app.py
```

Puis ouvrir:

```text
http://localhost:5000
```

L'application permet notamment:

- generation de notebook depuis un `.lng`
- nettoyage de fichier LINGO
- conversion `@OLE` -> explicite
- pipeline complet (conversion + cleaning + generation)
- export des donnees externes au format JSON ou DAT

---

## Utiliser le projet comme bibliotheque Python

Exemple type (dans un script a la racine du projet):

```python
import os
import sys

sys.path.insert(0, os.path.abspath("src"))

from lingo_parser.parser import parse_lingo_model
from lingo_parser.transformer import LingoModelTransformer2
from pyomo_generator.json_parser import (
    generate_pyomo_code,
    save_pyomo_data_to_json,
    save_pyomo_data_to_dat,
)
from notebook_generator.notebook_construct import generate_pyomo_notebook
from excel_parser.excel_module import convert_lingo_ole_to_explicit

# 1) Choisir le modele
ext_d = False
raw_file = "data/Philbrick.lng"

# 2) Convertir @OLE si besoin
explicit_file = convert_lingo_ole_to_explicit(raw_file)
file_to_parse = explicit_file
print(f"Fichier OLE converti: {explicit_file}")

# 3) Parser + transformer
tree = parse_lingo_model(file_to_parse)
model_dict = LingoModelTransformer2().transform(tree)

# 4) Generer le code Pyomo
pyomo_code = generate_pyomo_code(model_dict, external_data=ext_d)
print(pyomo_code)

# 5) (Optionnel) Export notebook
generate_pyomo_notebook(
    pyomo_code,
    solver="highs",
    filename="notebooks/Philbrick_from_api.ipynb",
    external_data=ext_d,
)

# 6) (Optionnel) Export des donnees externes
save_pyomo_data_to_json(model_dict, output_path="data/Philbrick_data.json")
save_pyomo_data_to_dat(model_dict, output_path="data/Philbrick_data.dat")

# Si vous voulez un code Pyomo qui lit des donnees externes:
pyomo_code_json = generate_pyomo_code(
    model_dict,
    external_data=True,
    data_filename="../data/Philbrick_data.json",
    external_data_format="json",
)

pyomo_code_dat = generate_pyomo_code(
    model_dict,
    external_data=True,
    data_filename="../data/Philbrick_data.dat",
    external_data_format="dat",
)
```

Remarques:

- `external_data=False`: les donnees sont integrees dans le code Pyomo.
- `external_data=True`: les donnees sont separees (JSON ou DAT) et rechargees par le notebook/code genere.

---

## Structure du projet

```text
lingo_to_pyomo/
├── src/
│   ├── lingo_parser/           # Grammaire + parser + transformer
│   ├── pyomo_generator/        # Generation code Pyomo + export JSON/DAT
│   ├── notebook_generator/     # Construction de notebooks
│   ├── excel_parser/           # Conversion @OLE
│   └── test/                   # Tests unitaires
├── dev/
│   ├── app.py                  # Application Flask
│   └── templates/              # Interface web
├── data/                       # Exemples .lng et fichiers de donnees
├── notebooks/                  # Notebooks generes
├── docs/                       # Documentation MkDocs
├── requirements.txt
└── README.md
```

---

## Tests

```bash
pytest src/test/ -v
```

---

## Documentation

```bash
mkdocs serve
```

Puis ouvrir `http://localhost:8000`.

---

## Auteurs

Fausto Errico - Virginie Destuynder - Joaquim Jusseau
