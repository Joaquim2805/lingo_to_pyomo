import mkdocs_gen_files
from pathlib import Path
import os
import sys

print("=== Running generate_api.py ===")

src_path = os.path.abspath("src")
print("SRC PATH =", src_path)
sys.path.append(src_path)

root = Path("src")
print("Scanning:", root)

py_files = sorted(root.rglob("*.py"))
print("FOUND FILES:", py_files)

# Titres lisibles par module (affiché dans la navigation)
MODULE_TITLES = {
    "lingo_parser": "LINGO Parser",
    "pyomo_generator": "Pyomo Generator",
    "notebook_generator": "Notebook Generator",
    "excel_parser": "Excel Parser",
}

nav = mkdocs_gen_files.Nav()

for path in py_files:
    module_path = path.relative_to(root).with_suffix("")
    parts = list(module_path.parts)

    # Exclure les fichiers de test et les fichiers __pycache__
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        continue
    if "test" in parts or "__pycache__" in parts:
        continue

    doc_path = Path("reference", *parts, "index.md")

    # Titre du module pour l'en-tête de la page
    module_name = parts[-1]
    package_name = parts[0] if len(parts) > 1 else module_name
    readable_package = MODULE_TITLES.get(package_name, package_name)
    readable_module = module_name.replace("_", " ").title()

    with mkdocs_gen_files.open(doc_path, "w") as f:
        ident = ".".join(parts)
        f.write(f"# `{ident}`\n\n")
        f.write(f"::: {ident}\n")
        f.write("    options:\n")
        f.write("      show_source: true\n")
        f.write("      show_root_heading: true\n")
        f.write("      heading_level: 2\n")

    # Navigation : chemin relatif à reference/SUMMARY.md (sans le préfixe reference/)
    nav_path = [readable_package, readable_module]
    nav[nav_path] = str(Path(*parts, "index.md"))

    mkdocs_gen_files.set_edit_path(doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
