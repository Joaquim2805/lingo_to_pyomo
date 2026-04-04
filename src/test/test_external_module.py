import sys
import os

src_path = os.path.abspath("./src/")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *
from pyomo_generator.json_parser import *
from notebook_generator.notebook_construct import *


from excel_parser.excel_module import *

from lingo_parser.lingo_cleaner import clean_lingo_content


from pyomo.opt import SolverFactory
from pyomo.environ import value


fichiers = [
    "California.lng",
    "forets.lng",
    "WINDOR_NONOLE.lng",
    "toysarus.lng",
    "Pastissimo.lng",
    "Regime_clean_explicit_test.lng",
    "Cargo_explicit_test.lng",
    "Cardoza_clean.lng",
    "Delivery_explicit_test.lng",
    "tp11.lng",
    "Eve-Steven.lng",
    "Progressive_clean.lng",
    "Buckly.lng",
    "Philbrick_explicit.lng",
    "Mercantile_explicit.lng",
    "Oxbridge_explicit.lng",
    "vetements_explicit.lng",
]

valeurs_optimales = [
    17,
    22333,
    36,
    230000,
    28095.00,
    90,
    13330,
    825,
    12,
    173,
    18,
    80000,
    1504,
    333680.0,
    7650000.0,
    1755.0,
    5325,
]


def test_external():

    temp = []

    for fichier, valeur_attendue in zip(fichiers, valeurs_optimales):
        tree = parse_lingo_model(f"./data/{fichier}")
        model_dict = LingoModelTransformer2().transform(tree)

        save_pyomo_data_to_json(model_dict)

        pyomo_code = generate_pyomo_code(model_dict, external_data=True)

        # print(pyomo_code)
        local_vars = {}
        exec(pyomo_code, local_vars)
        model = local_vars["model"]

        # Résout le modèle avec un solveur (par défaut glpk ou cbc)
        solver = SolverFactory("highs")  # ou 'cbc' si glpk n'est pas disponible
        result = solver.solve(model, tee=False)

        temp.append(int(value(model.obj)))

    assert temp == valeurs_optimales, (
        f"Les valeurs optimales devraient être {valeurs_optimales}, mais elles sont {temp}"
    )


def test_external_dat(tmp_path):
    """Valide le flux external_data avec un fichier DAT Pyomo/AMPL."""

    tree = parse_lingo_model("./data/California.lng")
    model_dict = LingoModelTransformer2().transform(tree)

    dat_path = tmp_path / "california_data.dat"
    save_pyomo_data_to_dat(model_dict, str(dat_path))

    pyomo_code = generate_pyomo_code(
        model_dict,
        external_data=True,
        data_filename=str(dat_path),
        external_data_format="dat",
    )

    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars["model"]

    solver = SolverFactory("highs")
    solver.solve(model, tee=False)

    assert int(value(model.obj)) == 17


def test_external_dat_cartesian_param(tmp_path):
    """Valide le chargement DAT natif Pyomo pour un parametre 2D (ex: QTEING)."""

    tree = parse_lingo_model("./data/Regime_clean_explicit_test.lng")
    model_dict = LingoModelTransformer2().transform(tree)

    dat_path = tmp_path / "regime_data.dat"
    save_pyomo_data_to_dat(model_dict, str(dat_path))

    pyomo_code = generate_pyomo_code(
        model_dict,
        external_data=True,
        data_filename=str(dat_path),
        external_data_format="dat",
    )

    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars["model"]

    solver = SolverFactory("highs")
    solver.solve(model, tee=False)

    assert int(value(model.obj)) == 90
