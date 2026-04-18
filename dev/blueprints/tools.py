"""Tool routes: generate, clean, OLE conversion, pipeline."""

import os
import traceback
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify

from config import DATA_FOLDER, OUTPUT_FOLDER
from services.file_manager import (
    list_lng_files,
    detect_ole_files,
    create_job,
    add_job_file,
    validate_file,
    save_upload,
    ALLOWED_LNG_EXTENSIONS,
    ALLOWED_EXCEL_EXTENSIONS,
)
from services.converter import (
    parse_and_generate,
    clean_file_content,
    convert_ole_file,
    run_pipeline,
    generate_notebook_file,
)

tools_bp = Blueprint("tools", __name__, url_prefix="/tools")


# ---------- Page ----------


@tools_bp.route("/")
def workspace():
    files = list_lng_files(DATA_FOLDER)
    ole_files = detect_ole_files(DATA_FOLDER, files)
    return render_template(
        "tools.html",
        nav_active="tools",
        files=files,
        ole_files=ole_files,
    )


# ---------- Generate notebook ----------


@tools_bp.route("/generate", methods=["POST"])
def generate():
    try:
        input_path = _resolve_input(request, "file_select", "file_upload")
        solver = request.form.get("solver_select", "highs")

        if not input_path:
            return jsonify(
                {"success": False, "error": "Aucun fichier sélectionné"}
            ), 400

        result = parse_and_generate(input_path, solver)

        job = create_job(
            "generate",
            metadata={
                "pyomo_code": result["pyomo_code"],
                "lingo_source": result["lingo_source"],
                "solver": solver,
                "file_name": Path(input_path).stem,
            },
        )

        return jsonify(
            {
                "success": True,
                "job_id": job["id"],
                "pyomo_code": result["pyomo_code"],
                "lingo_original": result["lingo_source"],
                "file_name": Path(input_path).stem,
                "solver": solver,
            }
        )
    except Exception as e:
        return _error_response("Erreur lors de la conversion", e)


# ---------- Clean ----------


@tools_bp.route("/clean", methods=["POST"])
def clean():
    try:
        input_path = _resolve_input(request, "file_select_clean", "file_upload_clean")

        if not input_path:
            return jsonify(
                {"success": False, "error": "Aucun fichier sélectionné"}
            ), 400

        result = clean_file_content(input_path)

        file_stem = Path(input_path).stem
        output_name = f"{file_stem}_clean.lng"
        output_path = str(DATA_FOLDER / output_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["cleaned"])

        job = create_job(
            "clean",
            metadata={
                "original": result["original"],
                "cleaned": result["cleaned"],
                "file_name": output_name,
            },
        )
        add_job_file(job["id"], output_name, output_path)

        return jsonify(
            {
                "success": True,
                "job_id": job["id"],
                "file_name": output_name,
                "content_preview": result["cleaned"],
                "original_content": result["original"],
                "original_size": result["original_size"],
                "cleaned_size": result["cleaned_size"],
            }
        )
    except Exception as e:
        return _error_response("Erreur lors du nettoyage", e)


# ---------- Convert OLE ----------


@tools_bp.route("/convert-ole", methods=["POST"])
def convert_ole():
    try:
        input_path = _resolve_input(request, "file_select_ole", "file_upload_ole")
        excel_path = _resolve_excel(request, "excel_upload_ole")

        if not input_path:
            return jsonify(
                {"success": False, "error": "Aucun fichier sélectionné"}
            ), 400

        result = convert_ole_file(input_path, excel_path=excel_path)

        output_name = Path(result["output_path"]).name
        job = create_job(
            "ole",
            metadata={
                "original": result["original"],
                "explicit": result["explicit"],
                "file_name": output_name,
            },
        )
        add_job_file(job["id"], output_name, result["output_path"])

        return jsonify(
            {
                "success": True,
                "job_id": job["id"],
                "file_name": output_name,
                "content_preview": result["explicit"][:2000],
                "original_content": result["original"][:2000],
            }
        )
    except Exception as e:
        return _error_response("Erreur lors de la conversion OLE", e)


# ---------- Pipeline ----------


@tools_bp.route("/pipeline", methods=["POST"])
def pipeline():
    try:
        input_path = _resolve_input(
            request, "file_select_pipeline", "file_upload_pipeline"
        )
        excel_path = _resolve_excel(request, "excel_upload_pipeline")
        solver = request.form.get("solver_select_pipeline", "highs")
        do_clean = request.form.get("do_clean") == "true"
        external_data = request.form.get("external_data") == "true"
        data_format = request.form.get("external_data_format", "json").lower().strip()

        if data_format.startswith("."):
            data_format = data_format[1:]
        if data_format not in {"json", "dat"}:
            data_format = "json"

        if not input_path:
            return jsonify(
                {"success": False, "error": "Aucun fichier sélectionné"}
            ), 400

        result = run_pipeline(
            input_path,
            solver,
            do_clean,
            external_data,
            data_format,
            excel_path=excel_path,
        )

        job = create_job(
            "pipeline",
            metadata={
                "pyomo_code": result["pyomo_code"],
                "lingo_source": result["lingo_source"],
                "solver": solver,
                "notebook_filename": result["notebook_filename"],
                "data_filename": result.get("data_filename"),
                "data_format": result.get("data_format"),
            },
        )
        add_job_file(job["id"], result["notebook_filename"], result["notebook_path"])
        if result.get("data_path"):
            add_job_file(job["id"], result["data_filename"], result["data_path"])

        return jsonify(
            {
                "success": True,
                "job_id": job["id"],
                "pipeline_steps": result["steps"],
                "notebook_filename": result["notebook_filename"],
                "data_filename": result.get("data_filename"),
                "data_format": result.get("data_format"),
                "has_ole": result["has_ole"],
                "was_cleaned": result["was_cleaned"],
                "has_external_data": result["has_external_data"],
                "pyomo_code_preview": result["pyomo_code"][:1500],
                # kept for backward compat with old frontend
                "notebook_path": result["notebook_path"],
                "data_path": result.get("data_path"),
                "json_path": result.get("data_path")
                if result.get("data_format") == "json"
                else None,
                "json_filename": result.get("data_filename")
                if result.get("data_format") == "json"
                else None,
            }
        )
    except Exception as e:
        return _error_response("Erreur lors du pipeline", e)


# ---------- Helpers ----------


def _resolve_input(req, select_name, upload_name=None):
    """Resolve the input file path from an upload or the dataset."""
    # Prefer upload if present
    if upload_name and upload_name in req.files:
        uploaded = req.files[upload_name]
        if uploaded and uploaded.filename:
            valid, _err = validate_file(uploaded, ALLOWED_LNG_EXTENSIONS)
            if valid:
                return save_upload(uploaded)

    # Fall back to dataset selection
    file_name = req.form.get(select_name)
    if file_name:
        path = str(DATA_FOLDER / file_name)
        if os.path.exists(path):
            return path

    return None


def _resolve_excel(req, upload_name):
    """Resolve an optional Excel upload; return saved path or None."""
    if upload_name and upload_name in req.files:
        uploaded = req.files[upload_name]
        if uploaded and uploaded.filename:
            valid, _err = validate_file(uploaded, ALLOWED_EXCEL_EXTENSIONS)
            if valid:
                return save_upload(uploaded)
    return None


def _error_response(message, exception):
    """Return a standardised JSON error payload."""
    print(f"{message}: {exception}")
    print(traceback.format_exc())
    return jsonify(
        {
            "success": False,
            "error": message,
            "details": str(exception),
            "type": type(exception).__name__,
            "traceback": traceback.format_exc(),
        }
    ), 500
