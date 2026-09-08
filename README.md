# LingoPy

[🇫🇷 Français](README.fr.md)

![Tests](https://github.com/Joaquim2805/lingo_to_pyomo/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

LingoPy converts LINGO optimization models (`.lng`) into Pyomo source code and Jupyter notebooks. It can be used in two ways:

- through the Flask web interface, to convert one or several files without writing code;
- through Python, to call the parser, Pyomo generator, cleaner, Excel `@OLE` conversion, and notebook generation separately.

Both modes use the same pipeline: the LINGO file is parsed, transformed into an intermediate model, and then converted into Pyomo code. The generated code can then be saved or included in a notebook.

## What the project does

The conversion pipeline is:

1. Read a LINGO file with the Lark grammar in `src/lingo_parser/lingogem.lark`.
2. Transform the parse tree into a Python dictionary containing sets, data, constraints, loops, and the objective.
3. Generate a Pyomo model as Python source code.
4. Optionally write model data to JSON or Pyomo/AMPL DAT format.
5. Optionally package the generated code, data loading, solve call, and result display in a Jupyter notebook.

Models containing `@OLE` can first be converted from Excel named ranges to explicit LINGO data.

## Installation

The repository is not packaged as an installable Python distribution. Run commands from the repository root and keep `src` importable as shown in the Python example below.

Python 3.10 or newer is required by the type-annotation syntax used in the source. Install the project dependencies in a virtual environment:

```bash
git clone https://github.com/Joaquim2805/lingo_to_pyomo.git
cd lingo_to_pyomo
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows cmd.exe
.venv\Scripts\activate.bat
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Generated models need an available Pyomo solver. The test suite uses HiGHS (`highs`); Gurobi, CPLEX, and GLPK can also be selected in the web interface when their local solver installation and, where applicable, license are available.

## Web interface

Start the Flask application from the repository root:

```bash
python dev/app.py
```

Open <http://127.0.0.1:5000>.

The interface accepts a model selected from `data/` or an uploaded `.lng` file. It provides:

- direct conversion to Pyomo code and a generated notebook;
- LINGO cleaning, which can be saved as a `_clean.lng` file;
- conversion of `@OLE` references using an optional uploaded Excel workbook;
- a full pipeline: optional OLE conversion, optional cleaning, parsing, Pyomo generation, optional JSON/DAT export, and notebook generation;
- batch processing of several models, with generated files grouped in a ZIP archive.

The pipeline stores generated notebooks in `notebooks/`, data files in `data/`, and uploaded/job files under `dev/uploads/`. The interface supports HiGHS, Gurobi, CPLEX, and GLPK as solver names; it does not install or validate those external solver executables.

## Python API

LingoPy is used directly from the repository rather than installed as a Python package. Add `src` to `sys.path`, then use the functions below:

- `parse_lingo_model(path)` parses a LINGO file and returns its syntax tree. `LingoModelTransformer2().transform(tree)` then converts that tree into the model's Python representation.
- `generate_pyomo_code(model_dict, external_data=False, data_filename=..., external_data_format=...)` returns Pyomo source code.
- `save_pyomo_data_to_json(...)` and `save_pyomo_data_to_dat(...)` export external data. `load_pyomo_data(...)` reads JSON data.
- `generate_pyomo_notebook(...)` writes a Jupyter notebook from generated Pyomo code.
- `clean_lingo_file(...)` and `clean_lingo_content(...)` clean LINGO input. `convert_lingo_ole_to_explicit(...)` replaces Excel `@OLE` data with explicit values.

### LINGO file to Pyomo code

This example uses the repository's `data/California.lng` model and produces a standalone Pyomo source string plus a notebook:

```python
import sys

sys.path.insert(0, "src")

from lingo_parser.parser import parse_lingo_model
from lingo_parser.transformer import LingoModelTransformer2
from notebook_generator.notebook_construct import generate_pyomo_notebook
from pyomo_generator.json_parser import generate_pyomo_code

input_path = "data/California.lng"
tree = parse_lingo_model(input_path)
model_dict = LingoModelTransformer2().transform(tree)

pyomo_code = generate_pyomo_code(model_dict)
print(pyomo_code)

generate_pyomo_notebook(
    pyomo_code,
    solver="highs",
    filename="notebooks/California_from_api.ipynb",
)
```

With `external_data=True`, export the data first and pass the same format and path to the generator:

```python
from pyomo_generator.json_parser import save_pyomo_data_to_json

data_path = save_pyomo_data_to_json(model_dict, "data/California_data.json")
pyomo_code = generate_pyomo_code(
    model_dict,
    external_data=True,
    data_filename=data_path,
    external_data_format="json",
)
```

For DAT output, use `save_pyomo_data_to_dat` and `external_data_format="dat"`. DAT models are generated as Pyomo `AbstractModel` instances and loaded with `create_instance`; JSON data is loaded by the generated helper.

## Supported LINGO syntax

The active grammar and transformer cover the following constructs:

- `MODEL:`, `SETS: ... ENDSETS`, `DATA: ... ENDDATA`, and `END`;
- `MAX` and `MIN` objectives;
- named sets, set elements, numeric and named ranges, and indexed/cartesian sets;
- scalar, one-dimensional, and multi-dimensional references;
- arithmetic with `+`, `-`, `*`, `/`, parentheses, and comparisons using `<=`, `>=`, and `=`;
- `@SUM`, including indexed expressions and conditional filters;
- `@FOR`, including nested loops and filters using `#GE#`, `#LE#`, `#GT#`, `#LT#`, `#EQ#`, `#NE#`, `#AND#`, and `#OR#`;
- `@BIN` for binary-variable inference and `@GIN` for integer-domain inference;
- `@OLE` syntax for the Excel conversion path.

`@ODBC` is recognized by the grammar but does not have an implemented ODBC data-loading path. When a LINGO function or expression is not recognized, LingoPy reports it in the generated Pyomo code with a `TODO` comment. The generated result must then be reviewed and completed manually.

## Limitations

- Unrecognized LINGO functions are reported with `TODO` comments in the generated Pyomo code; they are not converted automatically.
- A generated notebook needs Jupyter, Pyomo, and the selected solver installed locally.
- `@OLE` conversion is limited to Excel named ranges. The cleaner also changes the input text, so review a cleaned file before using it.

## Repository structure

```text
lingo_to_pyomo/
├── src/
│   ├── lingo_parser/           # Lark grammar, parser, transformer, cleaner
│   ├── pyomo_generator/        # Pyomo generation and JSON/DAT data export
│   ├── notebook_generator/     # Jupyter notebook generation
│   ├── excel_parser/           # Excel named-range and @OLE conversion
│   └── test/                   # pytest tests
├── dev/
│   ├── app.py                  # Flask entry point
│   ├── blueprints/             # Web routes, batch routes, and API routes
│   ├── services/               # Conversion and file-management services
│   └── templates/              # Flask templates
├── data/                       # LINGO examples and external data files
├── notebooks/                  # Generated and checked-in notebooks
├── docs/                       # MkDocs entry point and API-generation helper
├── requirements.txt
└── README.md
```

## Tests, notebooks, and documentation

Run the test suite from the repository root:

```bash
pytest src/test/ -v
```

The tests cover model generation and HiGHS solves, JSON/DAT external data, Excel/OLE conversion, and LINGO cleaning. The Excel tests write comparison files into `data/`.

The notebooks in `notebooks/` are examples or generated experiment files; they are not required for normal use. New notebooks can be produced through the web interface, the Python API, or the pipeline code.

Serve the MkDocs documentation with:

```bash
mkdocs serve
```

Then open <http://127.0.0.1:8000>. The API reference is generated from source docstrings by the MkDocs configuration.

## Authors

Fausto Errico, Virginie Destuynder, and Joaquim Jusseau.
