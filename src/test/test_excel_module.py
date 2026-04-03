import sys
import os
from pathlib import Path

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


def normalize_lingo(path):
    lines = []
    with open(path, "r") as f:
        for line in f:
            line = line.split("!")[0]  # enlève commentaires
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def test_excel_regime():

    convert_lingo_ole_to_explicit("./data/Regime.lng")

    with open("./data/Regime_explicit.lng", "r", encoding="utf-8") as f:
        content = f.read()

    cleaned_content = clean_lingo_content(content)

    # Écrire le fichier nettoyé
    with open("./data/Regime_explicit_clean.lng", "w", encoding="utf-8") as f:
        f.write(cleaned_content)

    f1 = normalize_lingo("./data/Regime_explicit_clean.lng")
    f2 = normalize_lingo("./data/Regime_clean_explicit_test.lng")

    assert f1 == f2


def test_excel_cargo():

    convert_lingo_ole_to_explicit("./data/Cargo.lng")

    with open("./data/Cargo_explicit.lng", "r", encoding="utf-8") as f:
        content = f.read()

    cleaned_content = clean_lingo_content(content)

    # Écrire le fichier nettoyé
    with open("./data/Cargo_explicit_clean.lng", "w", encoding="utf-8") as f:
        f.write(cleaned_content)

    f1 = normalize_lingo("./data/Cargo_explicit.lng")
    f2 = normalize_lingo("./data/Cargo_explicit_test.lng")

    assert f1 == f2


def test_excel_delivery():

    convert_lingo_ole_to_explicit("./data/Delivery.lng")

    f1 = normalize_lingo("./data/Delivery_explicit.lng")
    f2 = normalize_lingo("./data/Delivery_explicit_test.lng")

    assert f1 == f2


def test_excel_philbrick_parse_and_generate(tmp_path):

    explicit_path = convert_lingo_ole_to_explicit(
        "./data/Philbrick.lng", output_path=Path(tmp_path) / "Philbrick_explicit.lng"
    )

    tree = parse_lingo_model(explicit_path)
    model_dict = LingoModelTransformer2().transform(tree)
    pyomo_code = generate_pyomo_code(model_dict)

    cartesian_sets = {
        item["name"]: item["indices"]
        for item in model_dict["sets"]
        if "indices" in item
    }

    assert cartesian_sets["ARC1"] == ["PRODUITS", "REGION", "MOIS"]
    assert cartesian_sets["ARC4"] == [
        "PRODUITS",
        "MOIS",
        "USINES",
        "REGION",
        "PROCEDES",
    ]
    assert model_dict["data"]["revenu"] == [83.0, 112.0]
    assert model_dict["data"]["demande"] == [
        3600.0,
        6300.0,
        4900.0,
        4200.0,
        4500.0,
        5400.0,
        5100.0,
        6000.0,
    ]
    assert "model.revenu = Param(model.PRODUITS" in pyomo_code
    assert (
        "model.demande = Param(model.PRODUITS, model.REGION, model.MOIS" in pyomo_code
    )
    assert "model.ARC4 = Set(dimen=5" in pyomo_code
    assert (
        "model.X = Var(model.PRODUITS, model.MOIS, model.USINES, model.REGION, model.PROCEDES"
        in pyomo_code
    )
    assert "model.stock = Var(model.PRODUITS, model.USINES" in pyomo_code
