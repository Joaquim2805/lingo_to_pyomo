"""API routes for downloads and job info."""

import os

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime

from config import OUTPUT_FOLDER
from services.file_manager import get_job, create_batch_zip
from services.converter import generate_notebook_file

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/download/<job_id>/<file_type>", methods=["POST", "GET"])
def download(job_id, file_type):
    """Download a file produced by a job.

    file_type: 'notebook', 'data', 'lng', 'zip'
    """
    try:
        job = get_job(job_id)
        if not job:
            return jsonify({"success": False, "error": "Job non trouvé"}), 404

        meta = job.get("metadata", {})
        files = job.get("files", {})

        if file_type == "notebook":
            # Pipeline jobs already have a notebook on disk
            nb_name = meta.get("notebook_filename")
            if nb_name and nb_name in files:
                path = files[nb_name]
                if os.path.exists(path):
                    return send_file(path, as_attachment=True, download_name=nb_name)

            # Generate on-demand for 'generate' jobs
            pyomo_code = meta.get("pyomo_code")
            solver = meta.get("solver", "highs")
            stem = meta.get("file_name", "output")
            if not pyomo_code:
                return jsonify({"success": False, "error": "Code non disponible"}), 400

            nb_name = f"{stem}.ipynb"
            nb_path = str(OUTPUT_FOLDER / nb_name)

            ext_data = meta.get("data_filename") is not None
            data_fn = f"../data/{meta['data_filename']}" if ext_data else None
            data_fmt = meta.get("data_format", "json")

            generate_notebook_file(
                pyomo_code,
                solver,
                nb_path,
                external_data=ext_data,
                data_filename=data_fn,
                data_format=data_fmt,
            )
            return send_file(nb_path, as_attachment=True, download_name=nb_name)

        if file_type == "data":
            data_fn = meta.get("data_filename")
            if data_fn and data_fn in files:
                path = files[data_fn]
                if os.path.exists(path):
                    return send_file(path, as_attachment=True, download_name=data_fn)
            return jsonify(
                {"success": False, "error": "Fichier de données non trouvé"}
            ), 404

        if file_type in ("lng", "clean", "ole"):
            for name, path in files.items():
                if name.endswith(".lng") and os.path.exists(path):
                    return send_file(path, as_attachment=True, download_name=name)
            return jsonify({"success": False, "error": "Fichier .lng non trouvé"}), 404

        if file_type == "zip":
            zip_path = files.get("_batch.zip")
            if not zip_path:
                zip_path = create_batch_zip(job_id)
            if zip_path and os.path.exists(zip_path):
                stamp = datetime.now().strftime("%Y-%m-%d_%Hh%M")
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name=f"LingPy_batch_{stamp}.zip",
                )
            return jsonify({"success": False, "error": "Archive non trouvée"}), 404

        return jsonify({"success": False, "error": "Type de fichier invalide"}), 400

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": "Erreur lors du téléchargement",
                "details": str(e),
            }
        ), 500


@api_bp.route("/job/<job_id>")
def job_info(job_id):
    """Return non-sensitive job metadata."""
    job = get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job non trouvé"}), 404

    safe = {
        "id": job["id"],
        "type": job["type"],
        "created": job["created"],
        "status": job.get("status", "completed"),
        "files": list(job.get("files", {}).keys()),
        "metadata": {
            k: v for k, v in job.get("metadata", {}).items() if k not in ("model_dict",)
        },
    }
    return jsonify({"success": True, "job": safe})
