"""File management: uploads, validation, job tracking, ZIP creation."""

import json
import os
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from werkzeug.utils import secure_filename

from config import (
    UPLOAD_FOLDER,
    ALLOWED_LNG_EXTENSIONS,
    ALLOWED_EXCEL_EXTENSIONS,
)

# ---------------------------------------------------------------------------
# Disk-backed job store  (survives Flask auto-reload)
# ---------------------------------------------------------------------------
_JOBS_DIR = UPLOAD_FOLDER / ".jobs"
os.makedirs(_JOBS_DIR, exist_ok=True)


def _job_path(job_id: str) -> Path:
    return _JOBS_DIR / f"{job_id}.json"


def _save_job(job: dict):
    _job_path(job["id"]).write_text(
        json.dumps(job, ensure_ascii=False), encoding="utf-8"
    )


def _load_job(job_id: str) -> dict | None:
    p = _job_path(job_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def validate_file(file_storage, allowed_extensions):
    """Return (is_valid, error_message) for an uploaded file."""
    if not file_storage or not file_storage.filename:
        return False, "Aucun fichier sélectionné"

    ext = Path(file_storage.filename).suffix.lower()
    if ext not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        return False, f"Extension « {ext} » non autorisée. Acceptées : {allowed}"

    return True, None


def save_upload(file_storage, subfolder=None):
    """Save an uploaded file securely; return the saved path."""
    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError("Nom de fichier invalide")

    dest_dir = UPLOAD_FOLDER
    if subfolder:
        dest_dir = dest_dir / subfolder
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = dest_dir / filename
    file_storage.save(str(dest_path))
    return str(dest_path)


# ---------------------------------------------------------------------------
# Job management
# ---------------------------------------------------------------------------


def create_job(job_type, **kwargs):
    """Create a tracked job and return its dict."""
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "type": job_type,
        "created": datetime.now().isoformat(),
        "status": "completed",
        "files": {},
        "metadata": {},
        **kwargs,
    }
    _save_job(job)
    return job


def get_job(job_id):
    """Retrieve a job by its ID."""
    return _load_job(job_id)


def add_job_file(job_id, name, path):
    """Register a generated file inside a job."""
    job = _load_job(job_id)
    if job:
        job["files"][name] = str(path)
        _save_job(job)


def update_job(job):
    """Persist changes to an existing job dict."""
    _save_job(job)


def create_batch_zip(job_id):
    """Create a ZIP archive containing every file registered in a job."""
    job = _load_job(job_id)
    if not job:
        return None

    zip_filename = f"batch_{job_id}.zip"
    zip_path = str(UPLOAD_FOLDER / zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, path in job["files"].items():
            if name.startswith("_"):
                continue  # skip internal entries
            if os.path.exists(path):
                zf.write(path, arcname=name)

    # Persist zip path in job
    job["files"]["_batch.zip"] = zip_path
    _save_job(job)

    return zip_path


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------


def list_lng_files(data_folder):
    """List .lng files in the data folder, sorted alphabetically."""
    return sorted(f for f in os.listdir(data_folder) if f.endswith(".lng"))


def detect_ole_files(data_folder, files):
    """Return the subset of *files* whose content contains @OLE."""
    ole = []
    for f in files:
        try:
            text = (Path(data_folder) / f).read_text(encoding="utf-8", errors="ignore")
            if "@OLE" in text:
                ole.append(f)
        except Exception:
            pass
    return ole
