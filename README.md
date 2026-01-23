# LINGO → Pyomo Converter

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Convertisseur automatique de modèles d'optimisation LINGO vers Jupyter Pyomo

[Interface Web](#interface-web) | [Documentation](#documentation) | [Démarrage rapide](#démarrage-rapide) | [Contribution](#contribution)

</div>

---

## Description

LINGO → Pyomo est un outil pédagogique conçu pour faciliter la transition entre les langages LINGO et Pyomo dans l'enseignement en optimisation et recherche opérationnelle. Cet outil convertit automatiquement des modèles d'optimisation LINGO en notebooks Jupyter Pyomo prêts à l'exécution.




---

## Caractéristiques principales

| Fonctionnalité | Description |
|---|---|
| Parsing LINGO | Analyse complète de la syntaxe LINGO avec support complet du langage |
| Transformation AST | Conversion intermédiaire vers un format abstrait |
| Génération Pyomo | Création automatique du code Python équivalent |
| Sélection du solveur | Choix du solveur lors de la génération (Gurobi, CPLEX, GLPK, IPOPT) |
| Gestion d'erreurs | Retour détaillé avec stack trace complète |
| Interface web | Flask + Bootstrap 5 pour une expérience utilisateur professionnelle |
| Notebooks Jupyter | Export en fichier .ipynb directement utilisable |

---

## Quickstart


### Prérequis

- Python 3.8 ou supérieur
- Pip (gestionnaire de paquets Python)
- Un solveur : Gurobi, CPLEX, GLPK, HIGHS...

### Installation

#### 1. Cloner le dépôt

```bash
git clone https://github.com/Joaquim2805/lingo_to_pyomo.git
cd lingo_to_pyomo
```

#### 2. Créer un environnement virtuel

```bash
python -m venv .venv

# Sur Windows
.venv\Scripts\activate

# Sur macOS/Linux
source .venv/bin/activate
```

#### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### Utilisation

#### Lancer l'interface web

```bash
cd dev
python app.py
```

Puis ouvrir votre navigateur à : http://localhost:5000

#### Exemple d'utilisation

```python
from src.lingo_parser.parser import parse_lingo_model
from src.lingo_parser.transformer import LingoModelTransformer2
from src.pyomo_generator.json_parser import generate_pyomo_code
from src.notebook_generator.notebook_construct import generate_pyomo_notebook

# Charger et parser le modèle LINGO
tree = parse_lingo_model("model.lng")

# Transformer en représentation intermédiaire
model_dict = LingoModelTransformer2().transform(tree)

# Générer le code Pyomo
pyomo_code = generate_pyomo_code(model_dict)

# Exporter en notebook Jupyter
generate_pyomo_notebook(pyomo_code, solver="gurobi", filename="model.ipynb")
```

---

## Structure du projet

```
lingo_to_pyomo/
├── src/
│   ├── lingo_parser/
│   │   ├── lingo.lark          # Grammaire LINGO (Lark)
│   │   ├── parser.py           # Parser principal
│   │   └── transformer.py      # Transformation AST
│   ├── pyomo_generator/
│   │   └── json_parser.py      # Traduction JSON → Pyomo
│   ├── notebook_generator/
│   │   └── notebook_construct.py
│   └── test/
│       └── test_expmodel.py
├── dev/
│   ├── app.py                  # Application Flask
│   ├── templates/
│   │   └── index.html          # Interface web
│   └── static/
├── data/
│   └── *.lng                   # Modèles LINGO exemples
├── notebooks/                  # Notebooks Pyomo générés
├── docs/                       # Documentation API
├── requirements.txt
├── mkdocs.yml
└── README.md
```

---

## Architecture

### Pipeline de conversion

```
Fichier LINGO (.lng)
        ↓
    Lexer/Parser (Lark)
        ↓
    Abstract Syntax Tree (AST)
        ↓
    Transformer (LingoModelTransformer2)
        ↓
    Représentation intermédiaire (JSON)
        ↓
    Générateur Pyomo
        ↓
    Code Python (Pyomo)
        ↓
    Notebook Jupyter (.ipynb)
```

### Composants clés

| Composant | Rôle |
|-----------|------|
| Lark Parser | Parsing syntaxique basé sur grammaire formelle |
| Transformer | Conversion AST vers structure de données Python |
| JSON Parser | Traduction du modèle en code Pyomo |
| Notebook Generator | Construction de notebooks Jupyter exécutables |
| Flask App | Interface web pour l'accès utilisateur |

---

## Technologies utilisées

- Lark - Parser et grammaire formelle
- Pyomo - Framework d'optimisation
- Flask - Microframework web
- Jupyter - Notebooks interactifs
- Bootstrap 5 - Framework CSS



---

## Exemples de modèles

### Modèle linéaire simple

LINGO:
```lingo
MAX = 3*X + 2*Y;
X + Y <= 10;
X <= 8;
Y <= 6;
END
```

Pyomo généré:
```python
from pyomo.environ import *

model = ConcreteModel()
model.X = Var(bounds=(0, None))
model.Y = Var(bounds=(0, None))
model.obj = Objective(expr=3*model.X + 2*model.Y, sense=maximize)
model.c1 = Constraint(expr=model.X + model.Y <= 10)
model.c2 = Constraint(expr=model.X <= 8)
model.c3 = Constraint(expr=model.Y <= 6)
```

---


## Tests

Exécuter la suite de tests:

```bash
pytest src/test/ -v
```



## Documentation

Documentation complète disponible avec MkDocs:

```bash
mkdocs serve
```

---

## Dépannage

### Erreur "Module not found"

Assurez-vous que l'environnement virtuel est activé et que les dépendances sont installées:

```bash
pip install -r requirements.txt
```


### Port 5000 déjà utilisé

Modifiez le port dans `dev/app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)
```





## Auteurs

- Fausto Errico
- Virginie Destuynder
- Joaquim Jusseau

---

## Documentation supplémentaire

Pour des informations détaillées sur l'utilisation, consultez la [documentation complète](docs/).

---

<div align="center">

[Retour en haut](#lingo--pyomo-converter)

</div>
