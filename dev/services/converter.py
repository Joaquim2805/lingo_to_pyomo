"""Core conversion logic for LINGO → Pyomo transformations."""

import os
import traceback
from pathlib import Path

from config import DATA_FOLDER, OUTPUT_FOLDER

from lingo_parser.parser import parse_lingo_model
from lingo_parser.transformer import LingoModelTransformer2
from lingo_parser.lingo_cleaner import clean_lingo_content
from pyomo_generator.json_parser import (
    generate_pyomo_code,
    save_pyomo_data_to_json,
    save_pyomo_data_to_dat,
)
from notebook_generator.notebook_construct import generate_pyomo_notebook
from excel_parser.excel_module import convert_lingo_ole_to_explicit


def parse_and_generate(input_path, solver="highs"):
    """Parse a LINGO file and generate Pyomo code.

    Returns a dict with pyomo_code, lingo_source, model_dict, and solver.
    """
    tree = parse_lingo_model(input_path)
    model_dict = LingoModelTransformer2().transform(tree)
    pyomo_code = generate_pyomo_code(model_dict)

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        lingo_source = f.read()

    return {
        "pyomo_code": pyomo_code,
        "lingo_source": lingo_source,
        "model_dict": model_dict,
        "solver": solver,
    }


def clean_file_content(input_path):
    """Clean a LINGO file and return original + cleaned content."""
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    cleaned = clean_lingo_content(original)

    return {
        "original": original,
        "cleaned": cleaned,
        "original_size": len(original),
        "cleaned_size": len(cleaned),
    }


def convert_ole_file(input_path, excel_path=None):
    """Convert OLE references in a LINGO file to explicit data."""
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    output_path = convert_lingo_ole_to_explicit(input_path, excel_path=excel_path)

    with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
        explicit = f.read()

    return {
        "original": original,
        "explicit": explicit,
        "output_path": output_path,
    }


def run_pipeline(
    input_path,
    solver="highs",
    do_clean=False,
    external_data=True,
    data_format="json",
    excel_path=None,
):
    """Run the full LINGO → Pyomo conversion pipeline."""
    steps = []
    current_file = input_path
    file_stem = Path(input_path).stem

    with open(current_file, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    # Step 1: OLE detection and conversion
    has_ole = "@OLE" in original
    if has_ole:
        steps.append("Détection @OLE : conversion en format explicite")
        ole_output = convert_lingo_ole_to_explicit(current_file, excel_path=excel_path)
        current_file = ole_output
        with open(current_file, "r", encoding="utf-8", errors="ignore") as f:
            current_content = f.read()
    else:
        steps.append("Aucun @OLE détecté")
        current_content = original

    # Step 2: Cleaning
    if do_clean:
        steps.append("Nettoyage du fichier LINGO")
        cleaned = clean_lingo_content(current_content)
        cleaned_path = str(DATA_FOLDER / f"{file_stem}_pipeline_clean.lng")
        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        current_file = cleaned_path
    else:
        steps.append("Nettoyage non demandé")

    # Step 3: Parse
    steps.append("Parsing du modèle LINGO")
    tree = parse_lingo_model(current_file)
    model_dict = LingoModelTransformer2().transform(tree)

    # Step 4: Generate Pyomo code
    data_path = None
    data_filename = None

    if external_data:
        data_filename = f"{file_stem}_data.{data_format}"
        data_path = str(DATA_FOLDER / data_filename)

        if data_format == "dat":
            save_pyomo_data_to_dat(model_dict, data_path)
        else:
            save_pyomo_data_to_json(model_dict, data_path)

        steps.append(f"Données exportées ({data_format.upper()}) : {data_filename}")

        pyomo_code = generate_pyomo_code(
            model_dict,
            external_data=True,
            data_filename=f"../data/{data_filename}",
            external_data_format=data_format,
        )
    else:
        pyomo_code = generate_pyomo_code(model_dict, external_data=False)

    steps.append(
        f"Génération du code Pyomo (données {'externes' if external_data else 'intégrées'})"
    )

    # Step 5: Generate notebook
    notebook_filename = f"{file_stem}_pipeline.ipynb"
    notebook_path = str(OUTPUT_FOLDER / notebook_filename)

    generate_pyomo_notebook(
        pyomo_code,
        solver=solver,
        filename=notebook_path,
        external_data=external_data,
        data_filename=f"../data/{data_filename}" if external_data else None,
        external_data_format=data_format,
    )

    steps.append(f"Génération du notebook : {notebook_filename}")

    return {
        "steps": steps,
        "pyomo_code": pyomo_code,
        "lingo_source": original,
        "notebook_path": notebook_path,
        "notebook_filename": notebook_filename,
        "data_path": data_path,
        "data_filename": data_filename,
        "data_format": data_format if external_data else None,
        "has_ole": has_ole,
        "was_cleaned": do_clean,
        "has_external_data": external_data,
        "solver": solver,
    }


def generate_notebook_file(
    pyomo_code,
    solver,
    output_path,
    external_data=False,
    data_filename=None,
    data_format="json",
):
    """Generate a .ipynb notebook file from Pyomo code."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_pyomo_notebook(
        pyomo_code,
        solver=solver,
        filename=output_path,
        external_data=external_data,
        data_filename=data_filename,
        external_data_format=data_format,
    )
    return output_path
