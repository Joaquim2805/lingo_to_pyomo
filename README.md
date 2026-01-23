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

LINGO → Pyomo est un outil pédagogique conçu pour faciliter la transition entre les langages LINGO et Pyomo dans l'enseignement de l'optimisation. Cet outil convertit automatiquement des modèles d'optimisation LINGO en notebooks Jupyter Pyomo prêts à l'exécution.

**Public cible:** Enseignants, chercheurs, et étudiants en optimisation numérique qui souhaitent migrer de LINGO vers l'écosystème open-source Pyomo.

### Avantages principaux

- Automatisation complète de la conversion sans intervention manuelle
- Interface web intuitive et moderne
- Support de multiples solveurs (Gurobi, CPLEX, GLPK, IPOPT)
- Notebooks Jupyter prêts à l'emploi et exécutables
- Gestion d'erreurs détaillée avec diagnostics complets
- Licence open-source MIT

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

## Démarrage rapide

### Prérequis

- Python 3.8 ou supérieur
- Pip (gestionnaire de paquets Python)
- Un solveur optionnel : Gurobi, CPLEX, GLPK ou IPOPT

### Installation

#### 1. Cloner le dépôt

```bash
git clone https://github.com/joaquimjusseau/lingo_to_pyomo.git
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

#### Utilisation programmatique

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
- Font Awesome - Icônes vectorielles

### Solveurs supportés

- Gurobi (commercial, recommandé)
- CPLEX (IBM)
- GLPK (open-source)
- IPOPT (optimisation non-linéaire)

---

## Exemples de modèles supportés

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

## Interface web

L'application web offre une interface intuitive comprenant:

- Sélection de fichier parmi les modèles disponibles
- Choix du solveur (Gurobi, CPLEX, GLPK, IPOPT)
- Gestion des erreurs avec détails complets et stack trace
- Téléchargement direct du notebook .ipynb
- Design responsive compatible avec tous les appareils

Pour accéder à l'interface: http://localhost:5000

---

## Tests

Exécuter la suite de tests:

```bash
pytest src/test/ -v
```

Exécuter un fichier de test spécifique:

```bash
pytest src/test/test_expmodel.py -v
```

---

## Documentation

Documentation complète disponible dans le dossier `/docs` ou générez-la avec MkDocs:

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

### Erreur lors de la conversion

Consultez la modale d'erreur dans l'interface web. Elle affiche la stack trace complète pour diagnostiquer le problème.

### Port 5000 déjà utilisé

Modifiez le port dans `dev/app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

---

## Contribution

Les contributions sont bienvenues. Pour contribuer:

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nom-feature`)
3. Commit les changements (`git commit -m 'Description du changement'`)
4. Push vers la branche (`git push origin feature/nom-feature`)
5. Ouvrir une Pull Request

---

## Licence

Ce projet est licensé sous la MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

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
