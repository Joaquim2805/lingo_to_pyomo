from flask import Flask, render_template, request, send_file
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # dev/
PROJECT_ROOT = BASE_DIR.parent  # Lingo_to_Pyomo/
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from lingo_parser.parser import *
from lingo_parser.transformer import *
from notebook_generator.notebook_construct import *
from pyomo_generator.json_parser import *


app = Flask(__name__)

DATA_FOLDER = PROJECT_ROOT / "data"
OUTPUT_FOLDER = PROJECT_ROOT / "notebooks"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def generate_notebook(file_path, output_path, solver="gurobi"):
    """
    Génère un notebook Pyomo à partir d'un fichier LINGO donné.
    
    Args:
        file_path: Chemin vers le fichier LINGO
        output_path: Chemin de sortie du notebook
        solver: Solveur à utiliser (gurobi, cplex, glpk, ipopt) - par défaut gurobi
    """
    tree = parse_lingo_model(file_path)
    model_dict = LingoModelTransformer2().transform(tree)
    pyomo_code = generate_pyomo_code(model_dict)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_pyomo_notebook(pyomo_code, solver=solver, filename=output_path)


@app.route("/", methods=["GET"])
def index():
    # Lister les fichiers .lng du dossier DATA_FOLDER
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".lng")]
    return render_template("index.html", files=files)


@app.route("/generate", methods=["POST"])
def generate():
    file_name = request.form.get("file_select")
    solver = request.form.get("solver_select", "gurobi")
    
    if not file_name:
        return "Aucun fichier sélectionné !", 400

    input_path = os.path.join(DATA_FOLDER, file_name)
    output_path = os.path.join(OUTPUT_FOLDER, f"{Path(file_name).stem}.ipynb")

    generate_notebook(input_path, output_path, solver=solver)

    return send_file(output_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
