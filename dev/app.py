from flask import Flask, render_template, request, send_file, jsonify
import os
import sys
from pathlib import Path
import traceback

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
    try:
        file_name = request.form.get("file_select")
        solver = request.form.get("solver_select", "gurobi")
        
        if not file_name:
            return jsonify({
                "success": False,
                "error": "Aucun fichier sélectionné",
                "details": "Veuillez choisir un fichier LINGO dans la liste"
            }), 400

        input_path = os.path.join(DATA_FOLDER, file_name)
        
        # Vérifier que le fichier existe
        if not os.path.exists(input_path):
            return jsonify({
                "success": False,
                "error": "Fichier non trouvé",
                "details": f"Le fichier '{file_name}' n'existe pas"
            }), 404
        
        output_path = os.path.join(OUTPUT_FOLDER, f"{Path(file_name).stem}.ipynb")

        # Parser et transformer le modèle
        tree = parse_lingo_model(input_path)
        model_dict = LingoModelTransformer2().transform(tree)
        pyomo_code = generate_pyomo_code(model_dict)

        # Retourner un aperçu du code avec les infos de téléchargement
        return jsonify({
            "success": True,
            "pyomo_code": pyomo_code,
            "file_name": Path(file_name).stem,
            "solver": solver,
            "output_path": output_path
        }), 200
    
    except Exception as e:
        # Capturer toutes les erreurs et les retourner proprement
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"Erreur lors de la conversion: {error_message}")
        print(f"Stack trace:\n{error_traceback}")
        
        return jsonify({
            "success": False,
            "error": "Erreur lors de la conversion",
            "details": error_message,
            "type": type(e).__name__,
            "traceback": error_traceback
        }), 500


@app.route("/download", methods=["POST"])
def download():
    """Télécharge le notebook après que l'utilisateur ait validé l'aperçu."""
    try:
        data = request.get_json()
        file_name = data.get("file_name")
        solver = data.get("solver", "gurobi")
        pyomo_code = data.get("pyomo_code")
        
        if not file_name or not pyomo_code:
            return jsonify({
                "success": False,
                "error": "Données manquantes",
                "details": "Code ou nom de fichier manquant"
            }), 400
        
        output_path = os.path.join(OUTPUT_FOLDER, f"{file_name}.ipynb")
        
        # Générer le notebook
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        generate_pyomo_notebook(pyomo_code, solver=solver, filename=output_path)
        
        return send_file(output_path, as_attachment=True)
    
    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"Erreur lors du téléchargement: {error_message}")
        print(f"Stack trace:\n{error_traceback}")
        
        return jsonify({
            "success": False,
            "error": "Erreur lors du téléchargement",
            "details": error_message,
            "type": type(e).__name__,
            "traceback": error_traceback
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
