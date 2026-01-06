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

py_files = list(root.rglob("*.py"))
print("FOUND FILES:", py_files)

nav = mkdocs_gen_files.Nav()

for path in py_files:
    module_path = path.relative_to(root).with_suffix("")
    parts = list(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]

    doc_path = Path("reference", *parts, "index.md")
    nav_path = ["Référence API"] + parts

    with mkdocs_gen_files.open(doc_path, "w") as f:
        ident = ".".join(parts)
        f.write(f"# `{ident}`\n\n")
        f.write(f"::: {ident}\n")

    mkdocs_gen_files.set_edit_path(doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
