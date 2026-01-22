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
    nb_cells.append(
        new_markdown_cell("# 📘 Modèle Pyomo généré automatiquement")
    )

    # Imports
    nb_cells.append(
        new_markdown_cell("## 📦 Imports")
    )
    nb_cells.append(
        new_code_cell(
            "from pyomo.environ import *\n"
            "from pyomo.opt import SolverFactory"
        )
    )

    # Découpage du code Pyomo
    sections = split_pyomo_sections(pyomo_code)

    for title, code in sections:
        if not code.strip():
            continue

        nb_cells.append(
            new_markdown_cell(f"## 🔹 {title.title()}")
        )
        nb_cells.append(
            new_code_cell(code)
        )

    # Résolution
    nb_cells.append(
        new_markdown_cell("## ⚙️ Résolution du modèle")
    )
    nb_cells.append(
        new_code_cell(
            f"solver = SolverFactory('{solver}')\n"
            "result = solver.solve(model, tee=True)\n\n"
            "print('Solver status:', result.solver.status)\n"
            "print('Termination condition:', result.solver.termination_condition)"
        )
    )

    # Affichage des résultats
    nb_cells.append(
        new_markdown_cell("## 📊 Valeurs optimales des variables")
    )
    nb_cells.append(
        new_code_cell(
            "for v in model.component_objects(Var, active=True):\n"
            "    print(f'Variable set: {v.name}')\n"
            "    for index in v:\n"
            "        print(f'   {index} = {v[index].value}')"
        )
    )

    # Création du notebook
    nb = new_notebook(cells=nb_cells)

    with open(filename, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"✅ Notebook généré : {filename}")
