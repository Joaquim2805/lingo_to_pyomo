"""Main pages: home, about, compare, results."""

from flask import Blueprint, render_template, abort

from config import DATA_FOLDER
from services.file_manager import list_lng_files, detect_ole_files, get_job

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    files = list_lng_files(DATA_FOLDER)
    ole_files = detect_ole_files(DATA_FOLDER, files)
    return render_template(
        "home.html",
        nav_active="home",
        files=files,
        ole_files=ole_files,
    )


@main_bp.route("/about")
def about():
    return render_template("about.html", nav_active="about")


@main_bp.route("/compare/<job_id>")
def compare(job_id):
    job = get_job(job_id)
    if not job:
        abort(404)
    return render_template("compare.html", nav_active="tools", job=job)


@main_bp.route("/results/<job_id>")
def results(job_id):
    job = get_job(job_id)
    if not job:
        abort(404)
    return render_template("results.html", nav_active="tools", job=job)
