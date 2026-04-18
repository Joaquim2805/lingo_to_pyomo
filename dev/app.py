"""LingPy — Flask application: LINGO → Pyomo conversion tool.

Uses blueprints for multi-page architecture:
  main   →  /           home, about, compare, results
  tools  →  /tools/     generate, clean, OLE, pipeline
  batch  →  /batch/     multi-file batch processing
  api    →  /api/       downloads, job info
"""

import os

from flask import Flask, render_template, jsonify

import config  # noqa: F401  — ensures SRC_DIR on sys.path


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE
    app.config["UPLOAD_FOLDER"] = str(config.UPLOAD_FOLDER)
    app.secret_key = os.urandom(32)

    # ---- Blueprints ----
    from blueprints.main import main_bp
    from blueprints.tools import tools_bp
    from blueprints.batch import batch_bp
    from blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(api_bp)

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(
            {"success": False, "error": "Fichier trop volumineux (max 16 Mo)"}
        ), 413

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
