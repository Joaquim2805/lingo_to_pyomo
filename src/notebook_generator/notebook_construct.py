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
    pyomo_code: str, solver: str = "gurobi", filename: str = "model.ipynb"
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

    # Découpage du code Pyomo
    sections = split_pyomo_sections(pyomo_code)

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
