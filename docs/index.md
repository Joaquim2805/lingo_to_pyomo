#  Documentation Technique — LINGO → Pyomo

Bienvenue dans la documentation technique du projet **LINGO → Pyomo**.

Cette documentation est destinée aux développeurs souhaitant **comprendre**, **maintenir** ou **étendre** le projet.

---

## 🔹 À propos du projet

Ce projet est un convertisseur automatique de modèles LINGO vers des notebooks Pyomo.  
Il permet de transformer des modèles mathématiques écrits en LINGO en code Pyomo prêt à être exécuté.

Modules principaux :

- `lingo_parser` : analyse les fichiers LINGO et construit des arbres syntaxiques.
- `pyomo_generator` : produit automatiquement les modèles Pyomo à partir de la représentation interne.
- `notebook_generator` : crée des notebooks interactifs pour explorer et exécuter les modèles.

