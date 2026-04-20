"""Batch processing routes."""

import os
import traceback
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify

from config import DATA_FOLDER, OUTPUT_FOLDER
from services.file_manager import (
    list_lng_files,
    create_job,
    add_job_file,
    get_job,
    update_job,
    validate_file,
    save_upload,
    create_batch_zip,
    ALLOWED_LNG_EXTENSIONS,
    ALLOWED_EXCEL_EXTENSIONS,
)
from services.converter import parse_and_generate, generate_notebook_file, run_pipeline

batch_bp = Blueprint("batch", __name__, url_prefix="/batch")


@batch_bp.route("/")
def batch_page():
    files = list_lng_files(DATA_FOLDER)
    return render_template("batch.html", nav_active="batch", files=files)


@batch_bp.route("/process", methods=["POST"])
def process():
    try:
        solver = request.form.get("solver", "highs")
        do_clean = request.form.get("do_clean") in ("true", "on", "True")
        external_data = request.form.get("external_data") in ("true", "on", "True")
        data_format = request.form.get("external_data_format", "json")
        uploaded_files = request.files.getlist("files")
        dataset_files = request.form.getlist("dataset_files")

        # Excel pairing: excel_for_lng[i] = lng filename for excel_files[i]
        excel_uploads = request.files.getlist("excel_files")
        excel_lng_names = request.form.getlist("excel_for_lng")

        # Build a mapping: lng_filename -> saved excel path
        excel_map: dict[str, str] = {}
        for i, ef in enumerate(excel_uploads):
            if ef and ef.filename:
                valid, _ = validate_file(ef, ALLOWED_EXCEL_EXTENSIONS)
                if valid and i < len(excel_lng_names):
                    xlsx_path = save_upload(ef, subfolder="batch")
                    excel_map[excel_lng_names[i]] = xlsx_path

        # Gather all inputs: (display_name, lng_path, excel_path_or_None)
        input_files: list[tuple[str, str, str | None]] = []

        for f in uploaded_files:
            if f and f.filename:
                valid, _ = validate_file(f, ALLOWED_LNG_EXTENSIONS)
                if valid:
                    path = save_upload(f, subfolder="batch")
                    name = Path(f.filename).name
                    input_files.append((name, path, excel_map.get(name)))

        for name in dataset_files:
            path = str(DATA_FOLDER / name)
            if os.path.exists(path):
                input_files.append((name, path, None))

        if not input_files:
            return jsonify({"success": False, "error": "Aucun fichier à traiter"}), 400

        job = create_job("batch", metadata={"solver": solver, "items": []})
        results = []

        for name, path, excel_path in input_files:
            item: dict = {"name": name, "status": "pending"}
            try:
                result = run_pipeline(
                    path,
                    solver=solver,
                    do_clean=do_clean,
                    external_data=external_data,
                    data_format=data_format,
                    excel_path=excel_path,
                )

                nb_name = result["notebook_filename"]
                nb_path = result["notebook_path"]
                add_job_file(job["id"], nb_name, nb_path)

                if result.get("data_path"):
                    add_job_file(
                        job["id"], result["data_filename"], result["data_path"]
                    )

                item.update(
                    {
                        "status": "success",
                        "notebook": nb_name,
                        "pyomo_preview": result["pyomo_code"][:500],
                        "steps": result.get("steps", []),
                        "has_ole": result.get("has_ole", False),
                        "data_file": result.get("data_filename"),
                    }
                )
            except Exception as e:
                item.update({"status": "error", "error": str(e)})

            results.append(item)

        job["metadata"]["items"] = results
        # Reload from disk to get files added by add_job_file
        job = get_job(job["id"])
        job["metadata"]["items"] = results
        update_job(job)

        # Build ZIP of all produced notebooks
        create_batch_zip(job["id"])

        return jsonify(
            {
                "success": True,
                "job_id": job["id"],
                "results": results,
                "total": len(input_files),
                "succeeded": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] == "error"),
            }
        )
    except Exception as e:
        print(f"Batch error: {e}")
        print(traceback.format_exc())
        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du traitement par lot",
                "details": str(e),
                "traceback": traceback.format_exc(),
            }
        ), 500
