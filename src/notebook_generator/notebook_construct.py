import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
import re


def split_pyomo_sections(pyomo_code: str):
    """
    Découpe le code Pyomo en sections à partir des commentaires ======
    Retourne une liste de tuples (section_name, section_code)
    """

    sections = []
    current_title = "MODEL"
    current_lines = []

    for line in pyomo_code.splitlines():
        title_match = re.match(r"#\s*([A-Z ]+)", line)
        sep_match = re.match(r"#=+", line)

        if sep_match:
            continue

        if title_match and title_match.group(1).isupper():
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = title_match.group(1).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def generate_pyomo_notebook(
    pyomo_code: str,
    solver: str = "gurobi",
    filename: str = "model.ipynb",
    external_data: bool = False,
    json_data_filename: str = "./data/pyomo_data.json",
    data_filename: str = None,
    external_data_format: str = "json",
):
    """
    Génère un notebook Jupyter structuré avec une cellule par composant Pyomo.
    """

    nb_cells = []

    # Titre global
    nb_cells.append(new_markdown_cell("# 📘 Modèle Pyomo généré automatiquement"))

    # Imports
    nb_cells.append(new_markdown_cell("## 📦 Imports"))
    nb_cells.append(
        new_code_cell(
            "from pyomo.environ import *\n"
            "from pyomo.opt import SolverFactory\n"
            "import pandas as pd"
        )
    )

    effective_data_filename = data_filename or json_data_filename
    effective_data_format = (external_data_format or "json").strip().lower()
    if effective_data_format.startswith("."):
        effective_data_format = effective_data_format[1:]

    # ✨ CELLULE DONNÉES - Ajouter la fonction load_pyomo_data() directement si external_data=True
    if external_data and effective_data_format == "json":
        nb_cells.append(new_markdown_cell("## 💾 Charger les données"))
        load_data_code = f'''import json
import ast
from pathlib import Path

def load_pyomo_data(input_path="{effective_data_filename}"):
    """Charge les donnees externes depuis un fichier JSON."""
    input_file = Path(input_path)

    with open(input_file, "r") as f:
        data = json.load(f)

    def _convert_key(key):
        if not isinstance(key, str):
            return key
        if key.startswith("(") and key.endswith(")"):
            try:
                return ast.literal_eval(key)
            except Exception:
                return key
        try:
            return int(key)
        except Exception:
            return key

    # Convertir les dictionnaires de parametres indexes
    params = data.get("params", {{}})
    for pname, pval in list(params.items()):
        if isinstance(pval, dict):
            params[pname] = {{_convert_key(k): v for k, v in pval.items()}}

    cartesian = data.get("cartesian_data", {{}})
    for cname, cval in list(cartesian.items()):
        if isinstance(cval, dict):
            cartesian[cname] = {{_convert_key(k): v for k, v in cval.items()}}

    data["params"] = params
    data["cartesian_data"] = cartesian
    return data

# Charger les données
data = load_pyomo_data()'''
        nb_cells.append(new_code_cell(load_data_code))
    elif external_data and effective_data_format == "dat":
        nb_cells.append(
            new_markdown_cell(
                "## 💾 Chargement des données\n"
                "Les données `.dat` sont chargées nativement par Pyomo via `model.create_instance(...)` dans la section du modèle."
            )
        )

    # Découpage du code Pyomo
    # Nettoyer le code pour supprimer les imports problématiques
    cleaned_code = "\n".join(
        line
        for line in pyomo_code.split("\n")
        if "from pyomo_generator.json_parser import load_pyomo_data" not in line
        and "data = load_pyomo_data(" not in line
    )

    sections = split_pyomo_sections(cleaned_code)

    for title, code in sections:
        if not code.strip():
            continue

        nb_cells.append(new_markdown_cell(f"## 🔹 {title.title()}"))
        nb_cells.append(new_code_cell(code))

    # Résolution
    nb_cells.append(new_markdown_cell("## ⚙️ Résolution du modèle"))
    nb_cells.append(
        new_code_cell(
            f"solver = SolverFactory('{solver}')\n"
            "result = solver.solve(model, tee=True)\n\n"
            "print('✅ Solver status:', result.solver.status)\n"
            "print('✅ Termination condition:', result.solver.termination_condition)"
        )
    )

    # Valeur objective
    nb_cells.append(new_markdown_cell("## 🎯 Valeur de la fonction objective"))
    nb_cells.append(
        new_code_cell(
            "for obj in model.component_objects(Objective, active=True):\n"
            "    print(f'Objectif: {obj.name}')\n"
            "    print(f'Valeur optimale: {obj():.4f}')\n"
            '    print(f\'Sens: {"Minimisation" if obj.sense == minimize else "Maximisation"}\')'
        )
    )

    # Affichage des résultats
    nb_cells.append(new_markdown_cell("## 📊 Valeurs optimales des variables"))
    nb_cells.append(
        new_code_cell(
            "# Extraction des résultats dans un DataFrame\n"
            "results_data = []\n"
            "for v in model.component_objects(Var, active=True):\n"
            "    for index in v:\n"
            "        results_data.append({\n"
            "            'Variable': v.name,\n"
            "            'Index': str(index) if index != None else '-',\n"
            "            'Valeur': v[index].value\n"
            "        })\n\n"
            "df_results = pd.DataFrame(results_data)\n"
            "# Filtrer les valeurs non-nulles pour plus de clarté\n"
            "df_results = df_results[df_results['Valeur'].notna()]\n"
            "df_results = df_results[df_results['Valeur'] != 0]\n"
            "df_results.style.format({'Valeur': '{:.4f}'}).set_caption('Variables de décision optimales')"
        )
    )

    # Création du notebook
    nb = new_notebook(cells=nb_cells)

    with open(filename, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"✅ Notebook généré : {filename}")
