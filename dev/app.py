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
from excel_parser.excel_module import convert_lingo_ole_to_explicit
from lingo_parser.lingo_cleaner import clean_lingo_content


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

    # Identifier les fichiers avec des correspondances Excel
    ole_files = []
    for lng_file in files:
        lng_path = DATA_FOLDER / lng_file
        lng_text = lng_path.read_text(encoding="utf-8", errors="ignore")
        # Chercher si le fichier contient @OLE
        if "@OLE" in lng_text:
            ole_files.append(lng_file)

    return render_template("index.html", files=files, ole_files=ole_files)


@app.route("/generate", methods=["POST"])
def generate():
    try:
        file_name = request.form.get("file_select")
        solver = request.form.get("solver_select", "gurobi")

        if not file_name:
            return jsonify(
                {
                    "success": False,
                    "error": "Aucun fichier sélectionné",
                    "details": "Veuillez choisir un fichier LINGO dans la liste",
                }
            ), 400

        input_path = os.path.join(DATA_FOLDER, file_name)

        # Vérifier que le fichier existe
        if not os.path.exists(input_path):
            return jsonify(
                {
                    "success": False,
                    "error": "Fichier non trouvé",
                    "details": f"Le fichier '{file_name}' n'existe pas",
                }
            ), 404

        output_path = os.path.join(OUTPUT_FOLDER, f"{Path(file_name).stem}.ipynb")

        # Parser et transformer le modèle
        tree = parse_lingo_model(input_path)
        model_dict = LingoModelTransformer2().transform(tree)
        pyomo_code = generate_pyomo_code(model_dict)

        # Retourner un aperçu du code avec les infos de téléchargement
        return jsonify(
            {
                "success": True,
                "pyomo_code": pyomo_code,
                "file_name": Path(file_name).stem,
                "solver": solver,
                "output_path": output_path,
            }
        ), 200

    except Exception as e:
        # Capturer toutes les erreurs et les retourner proprement
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors de la conversion: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors de la conversion",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


@app.route("/clean", methods=["POST"])
def clean():
    """
    Nettoie un fichier LINGO en supprimant les commentaires entre crochets,
    en normalisant la casse des identifiants, et en supprimant les sections
    DATA ENDATA vides.
    """
    try:
        file_name = request.form.get("file_select_clean")

        if not file_name:
            return jsonify(
                {
                    "success": False,
                    "error": "Aucun fichier sélectionné",
                    "details": "Veuillez choisir un fichier LINGO à nettoyer",
                }
            ), 400

        input_path = os.path.join(DATA_FOLDER, file_name)

        # Vérifier que le fichier existe
        if not os.path.exists(input_path):
            return jsonify(
                {
                    "success": False,
                    "error": "Fichier non trouvé",
                    "details": f"Le fichier '{file_name}' n'existe pas",
                }
            ), 404

        # Lire et nettoyer le fichier
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        cleaned_content = clean_lingo_content(content)

        # Générer le chemin de sortie
        file_stem = Path(file_name).stem
        output_name = f"{file_stem}_clean.lng"
        output_path = str(DATA_FOLDER / output_name)

        # Écrire le fichier nettoyé
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        # Afficher un aperçu du contenu nettoyé
        preview = (
            cleaned_content[:1500] + "..."
            if len(cleaned_content) > 1500
            else cleaned_content
        )

        return jsonify(
            {
                "success": True,
                "file_name": output_name,
                "output_path": output_path,
                "content_preview": preview,
                "original_size": len(content),
                "cleaned_size": len(cleaned_content),
            }
        ), 200

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors du nettoyage: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du nettoyage",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


@app.route("/convert-ole", methods=["POST"])
def convert_ole():
    """
    Convertit un fichier LINGO OLE en version explicite en remplaçant
    les appels @OLE par les données du fichier Excel correspondant.
    """
    try:
        file_name = request.form.get("file_select_ole")

        if not file_name:
            return jsonify(
                {
                    "success": False,
                    "error": "Aucun fichier sélectionné",
                    "details": "Veuillez choisir un fichier LINGO à convertir",
                }
            ), 400

        input_path = str(DATA_FOLDER / file_name)

        # Vérifier que le fichier existe
        if not os.path.exists(input_path):
            return jsonify(
                {
                    "success": False,
                    "error": "Fichier non trouvé",
                    "details": f"Le fichier '{file_name}' n'existe pas",
                }
            ), 404

        # Appeler la fonction de conversion
        output_path = convert_lingo_ole_to_explicit(input_path)

        # Lire le fichier généré
        with open(output_path, "r", encoding="utf-8") as f:
            explicit_content = f.read()

        # Retourner le contenu et le chemin
        return jsonify(
            {
                "success": True,
                "file_name": os.path.basename(output_path),
                "output_path": output_path,
                "content_preview": explicit_content[:1000] + "..."
                if len(explicit_content) > 1000
                else explicit_content,
            }
        ), 200

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors de la conversion OLE: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors de la conversion OLE",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


@app.route("/download", methods=["POST"])
def download():
    """Télécharge le notebook après que l'utilisateur ait validé l'aperçu."""
    try:
        data = request.get_json()
        file_name = data.get("file_name")
        solver = data.get("solver", "gurobi")
        pyomo_code = data.get("pyomo_code")

        if not file_name or not pyomo_code:
            return jsonify(
                {
                    "success": False,
                    "error": "Données manquantes",
                    "details": "Code ou nom de fichier manquant",
                }
            ), 400

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

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du téléchargement",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


@app.route("/download-ole", methods=["POST"])
def download_ole():
    """Télécharge le fichier .lng converti de OLE en explicite."""
    try:
        data = request.get_json()
        output_path = data.get("output_path")
        file_name = data.get("file_name")

        if not output_path or not file_name:
            return jsonify({"success": False, "error": "Données manquantes"}), 400

        # Vérifier que le fichier existe
        if not os.path.exists(output_path):
            return jsonify({"success": False, "error": "Fichier non trouvé"}), 404

        return send_file(output_path, as_attachment=True, download_name=file_name)

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors du téléchargement OLE: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du téléchargement",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
