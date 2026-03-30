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
