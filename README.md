# LINGO → Pyomo

<div align="center">

![Tests](https://github.com/Joaquim2805/lingo_to_pyomo/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Convertisseur automatique de modèles LINGO vers notebooks Jupyter Pyomo

</div>

---

## Description

Outil pédagogique pour convertir automatiquement des modèles d'optimisation LINGO en notebooks Jupyter Pyomo prêts à l'exécution. Simplifie la transition entre LINGO et Pyomo dans l'enseignement de la recherche opérationnelle.

---

## Installation

```bash
git clone https://github.com/Joaquim2805/lingo_to_pyomo.git
cd lingo_to_pyomo
python -m venv .venv
```

Activer l'environnement virtuel :

```bash
# Sur macOS/Linux
source .venv/bin/activate

# Sur Windows
.venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

**Prérequis** : Python 3.8+ et un solveur d'optimisation (Gurobi, CPLEX, GLPK, HiGHS...)

---

## Utilisation

### Interface Web

```bash
cd dev
python app.py
```

Accéder à http://localhost:5000

### API Python

```python
from src.lingo_parser.parser import parse_lingo_model
from src.lingo_parser.transformer import LingoModelTransformer2
from src.pyomo_generator.json_parser import generate_pyomo_code
from src.notebook_generator.notebook_construct import generate_pyomo_notebook

# Parser le modèle LINGO
tree = parse_lingo_model("model.lng")

# Transformer en structure intermédiaire
model_dict = LingoModelTransformer2().transform(tree)

# Générer le code Pyomo
pyomo_code = generate_pyomo_code(model_dict)

# Exporter en notebook Jupyter
generate_pyomo_notebook(pyomo_code, solver="highs", filename="model.ipynb")
```

---

## Fonctionnalités

- Parsing complet de la syntaxe LINGO avec grammaire formelle (Lark)
- Transformation AST vers représentation intermédiaire
- Génération automatique de code Pyomo
- Support des ensembles, paramètres, variables et contraintes
- Gestion des boucles `@FOR` et expressions `@SUM`
- Support des données externes Excel avec `@OLE`
- Export en notebooks Jupyter structurés et formatés
- Choix du solveur (Gurobi, CPLEX, GLPK, HiGHS, IPOPT...)
- Interface web Flask avec Bootstrap 5
- Visualisation des résultats avec pandas

---

## Architecture

```
Fichier LINGO (.lng)
    ↓  Parser (Lark)
AST
    ↓  Transformer
Représentation Python
    ↓  Générateur
Code Pyomo
    ↓  Notebook Generator
Jupyter Notebook (.ipynb)
```

### Structure du projet

```
lingo_to_pyomo/
├── src/
│   ├── lingo_parser/
│   │   ├── lingo.lark          # Grammaire LINGO (Lark)
│   │   ├── parser.py           # Parser principal
│   │   └── transformer.py      # Transformation AST
│   ├── pyomo_generator/
│   │   └── json_parser.py      # Traduction vers Pyomo
│   ├── notebook_generator/
│   │   └── notebook_construct.py
│   ├── excel_parser/
│   │   └── excel_module.py     # Support @OLE Excel
│   └── test/
│       └── test_*.py           # Tests unitaires
├── dev/
│   ├── app.py                  # Application Flask
│   └── templates/
│       └── index.html          # Interface web
├── data/
│   └── *.lng                   # Modèles LINGO exemples
├── notebooks/                  # Notebooks générés
├── docs/                       # Documentation
├── requirements.txt
├── mkdocs.yml
└── README.md
```

---

## Exemple

**Entrée LINGO** (`model.lng`) :

```lingo
MAX = 3*X + 2*Y;
X + Y <= 10;
X <= 8;
Y <= 6;
END
```

**Sortie Pyomo** (dans notebook) :

```python
from pyomo.environ import *

model = ConcreteModel()
model.X = Var(domain=NonNegativeReals)
model.Y = Var(domain=NonNegativeReals)
model.obj = Objective(expr=3*model.X + 2*model.Y, sense=maximize)
model.c1 = Constraint(expr=model.X + model.Y <= 10)
model.c2 = Constraint(expr=model.X <= 8)
model.c3 = Constraint(expr=model.Y <= 6)
```

---

## Tests

```bash
pytest src/test/ -v
```

---

## Documentation

Générer et consulter la documentation avec MkDocs :

```bash
mkdocs serve
```

Puis accéder à http://localhost:8000

---

## Technologies

- **Lark** : Parser et grammaire formelle
- **Pyomo** : Framework d'optimisation Python
- **Flask** : Interface web
- **Jupyter** : Notebooks interactifs
- **pandas** : Visualisation des résultats

---

## Auteurs

Fausto Errico • Virginie Destuynder • Joaquim Jusseau
