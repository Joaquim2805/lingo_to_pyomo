# 📚 Documentation Technique — LINGO → Pyomo

Bienvenue dans la documentation technique du projet **LINGO → Pyomo**.

Cette documentation est destinée aux développeurs souhaitant **comprendre**, **maintenir** ou **étendre** le projet. Elle décrit la structure du code et les modules du convertisseur automatique.

---

## 🔹 À propos du projet

Ce projet est un convertisseur automatique de modèles LINGO vers des notebooks Pyomo.  
Il permet de transformer des modèles d’optimisation écrits en LINGO en code Pyomo prêt à être exécuté.

Modules principaux :

- `lingo_parser` : analyse les fichiers LINGO et construit des arbres syntaxiques.
- `pyomo_generator` : produit automatiquement les modèles Pyomo à partir de la représentation interne.
- `notebook_generator` : crée des notebooks interactifs pour explorer et exécuter les modèles.
- Modules utilitaires pour le parsing JSON et la manipulation des données.

---

## 🔹 Fonctionnement de la documentation

La documentation est générée automatiquement avec :

- **MkDocs** pour la structure et le rendu web.
- **Material for MkDocs** pour le thème et la navigation.
- **mkdocstrings** pour extraire les docstrings du code et produire les pages API.

Chaque page de l’API montre :

- Les modules et classes.
- Les fonctions avec leurs signatures et docstrings.
- Le code source annoté.

---
