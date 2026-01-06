import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell


def generate_pyomo_notebook(
    pyomo_code: str, solver: str = "gurobi", filename: str = "model.ipynb"
):
    """
    Génère un notebook Jupyter contenant le modèle Pyomo, la résolution et l'affichage des résultats.

    Args:
        pyomo_code (str): Le code Pyomo généré par `generate_pyomo_code`.
        solver (str): Le solveur à utiliser (ex: 'gurobi', 'glpk', 'cplex').
        filename (str): Nom du notebook de sortie.

    Returns:
        None (sauvegarde un fichier .ipynb)
    """

    nb = new_notebook(
        cells=[
            new_markdown_cell("# 📘 Modèle Pyomo généré automatiquement"),
            new_code_cell(
                "from pyomo.environ import *\nfrom pyomo.opt import SolverFactory\n"
            ),
            new_markdown_cell("## Définition du modèle"),
            new_code_cell(pyomo_code),
            new_markdown_cell("## Résolution du modèle"),
            new_code_cell(
                f"solver = SolverFactory('{solver}')  # change selon ce que tu as installé\n"
                "result = solver.solve(model, tee=True)\n"
                "print('Solver status:', result.solver.status)\n"
                "print('Termination condition:', result.solver.termination_condition)\n"
            ),
            new_markdown_cell("## Valeurs optimales des variables"),
            new_code_cell(
                "for v in model.component_objects(Var, active=True):\n"
                "    print(f'Variable set: {v}')\n"
                "    for index in v:\n"
                "        print(f'   {index} = {v[index].value}')\n"
            ),
        ]
    )

    # Sauvegarde du notebook
    with open(filename, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"✅ Notebook généré : {filename}")
