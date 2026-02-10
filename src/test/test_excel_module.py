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
