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

        # Lire le contenu LINGO original pour la comparaison
        try:
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                lingo_original = f.read()
        except Exception:
            lingo_original = None

        # Retourner un aperçu du code avec les infos de téléchargement
        return jsonify(
            {
                "success": True,
                "pyomo_code": pyomo_code,
                "lingo_original": lingo_original,
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

        # Aperçu du contenu original
        original_preview = content[:1500] + "..." if len(content) > 1500 else content

        return jsonify(
            {
                "success": True,
                "file_name": output_name,
                "output_path": output_path,
                "content_preview": preview,
                "original_content": original_preview,
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

        # Lire le fichier original
        with open(input_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Lire le fichier généré
        with open(output_path, "r", encoding="utf-8") as f:
            explicit_content = f.read()

        # Aperçu du contenu original
        original_preview = (
            original_content[:1500] + "..."
            if len(original_content) > 1500
            else original_content
        )

        # Retourner le contenu et le chemin
        return jsonify(
            {
                "success": True,
                "file_name": os.path.basename(output_path),
                "output_path": output_path,
                "content_preview": explicit_content[:1500] + "..."
                if len(explicit_content) > 1500
                else explicit_content,
                "original_content": original_preview,
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


@app.route("/pipeline", methods=["POST"])
def pipeline():
    """Pipeline complet: détection Excel, conversion OLE, cleaning, génération notebook avec données externes."""
    try:
        file_name = request.form.get("file_select_pipeline")
        solver = request.form.get("solver_select_pipeline", "gurobi")
        do_clean = request.form.get("do_clean") == "true"
        external_data = request.form.get("external_data") == "true"

        if not file_name:
            return jsonify(
                {
                    "success": False,
                    "error": "Aucun fichier sélectionné",
                    "details": "Veuillez choisir un fichier LINGO dans la liste",
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

        pipeline_steps = []
        current_file = input_path

        # Lire le contenu original
        with open(current_file, "r", encoding="utf-8", errors="ignore") as f:
            original_content = f.read()

        # Étape 1: Détecter et convertir @OLE si présent
        has_ole = "@OLE" in original_content
        if has_ole:
            pipeline_steps.append("🔄 Détection @OLE: Conversion en format explicite")
            ole_output = convert_lingo_ole_to_explicit(current_file)
            current_file = ole_output
            with open(current_file, "r", encoding="utf-8", errors="ignore") as f:
                current_content = f.read()
        else:
            pipeline_steps.append("✓ Aucun @OLE détecté")
            current_content = original_content

        # Étape 2: Nettoyage si demandé
        if do_clean:
            pipeline_steps.append("🧹 Nettoyage du fichier LINGO")
            cleaned_content = clean_lingo_content(current_content)

            # Sauvegarder le fichier nettoyé
            file_stem = Path(file_name).stem
            cleaned_filename = f"{file_stem}_pipeline_clean.lng"
            cleaned_path = str(DATA_FOLDER / cleaned_filename)
            with open(cleaned_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)
            current_file = cleaned_path
            current_content = cleaned_content
        else:
            pipeline_steps.append("○ Nettoyage non demandé")

        # Étape 3: Parser et transformer le modèle
        pipeline_steps.append("🔍 Parsing du modèle LINGO")
        tree = parse_lingo_model(current_file)
        model_dict = LingoModelTransformer2().transform(tree)

        # Étape 4: Génération du code Pyomo
        pipeline_steps.append(
            f"⚙️ Génération du code Pyomo (données {'externes' if external_data else 'intégrées'})"
        )

        json_path = None
        if external_data:
            # Sauvegarder les données en JSON
            json_filename = f"{Path(file_name).stem}_data.json"
            json_path = str(DATA_FOLDER / json_filename)
            save_pyomo_data_to_json(model_dict, json_path)
            pipeline_steps.append(f"💾 Données exportées: {json_filename}")

            # Générer le code avec external_data=True
            pyomo_code = generate_pyomo_code(
                model_dict, external_data=True, data_filename=f"../data/{json_filename}"
            )
        else:
            pyomo_code = generate_pyomo_code(model_dict, external_data=False)

        # Étape 5: Générer le notebook
        notebook_filename = f"{Path(file_name).stem}_pipeline.ipynb"
        notebook_path = str(OUTPUT_FOLDER / notebook_filename)
        pipeline_steps.append(f"📓 Génération du notebook: {notebook_filename}")

        generate_pyomo_notebook(
            pyomo_code,
            solver=solver,
            filename=notebook_path,
            external_data=external_data,
            json_data_filename=f"../data/{Path(file_name).stem}_data.json"
            if external_data
            else None,
        )

        return jsonify(
            {
                "success": True,
                "pipeline_steps": pipeline_steps,
                "notebook_path": notebook_path,
                "notebook_filename": notebook_filename,
                "json_path": json_path,
                "json_filename": Path(json_path).name if json_path else None,
                "has_ole": has_ole,
                "was_cleaned": do_clean,
                "has_external_data": external_data,
                "pyomo_code_preview": pyomo_code[:1000] + "..."
                if len(pyomo_code) > 1000
                else pyomo_code,
            }
        ), 200

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors du pipeline: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du pipeline",
                "details": error_message,
                "type": type(e).__name__,
                "traceback": error_traceback,
            }
        ), 500


@app.route("/download-pipeline", methods=["POST"])
def download_pipeline():
    """Télécharge les fichiers générés par le pipeline (notebook + JSON si applicable)."""
    try:
        data = request.get_json()
        notebook_path = data.get("notebook_path")
        json_path = data.get("json_path")
        download_type = data.get("download_type", "notebook")  # "notebook" ou "json"

        if download_type == "notebook":
            if not notebook_path or not os.path.exists(notebook_path):
                return jsonify({"success": False, "error": "Notebook non trouvé"}), 404
            return send_file(notebook_path, as_attachment=True)

        elif download_type == "json":
            if not json_path or not os.path.exists(json_path):
                return jsonify(
                    {"success": False, "error": "Fichier JSON non trouvé"}
                ), 404
            return send_file(json_path, as_attachment=True)

        else:
            return jsonify(
                {"success": False, "error": "Type de téléchargement invalide"}
            ), 400

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()

        print(f"Erreur lors du téléchargement pipeline: {error_message}")
        print(f"Stack trace:\n{error_traceback}")

        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du téléchargement",
                "details": error_message,
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
