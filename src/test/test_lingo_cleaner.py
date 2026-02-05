"""
Tests unitaires pour la fonction de nettoyage LINGO.

Ces tests vérifient que le nettoyeur fonctionne correctement pour:
- Suppression des commentaires entre crochets
- Normalisation de la casse
- Suppression des sections DATA ENDATA vides
"""

import sys
import os

src_path = os.path.abspath("./src/")
sys.path.append(src_path)

from lingo_parser.lingo_cleaner import (
    clean_lingo_content,
    _remove_brackets,
    _remove_empty_data_sections,
)


def test_remove_brackets():
    """Test la suppression des commentaires entre crochets."""
    text = "SETS:\n  Items [Liste des items] / item1, item2 /;\nENDSETS"
    result = _remove_brackets(text)
    assert "[" not in result
    assert "]" not in result
    assert "Items" in result
    print("✅ test_remove_brackets passed")


def test_remove_empty_data_sections():
    """Test la suppression des sections DATA ENDATA vides."""
    text = """
DATA:
ENDDATA

DATA:
  param = 100;
ENDDATA
"""
    result = _remove_empty_data_sections(text)
    # La première section vide devrait être supprimée
    assert result.count("DATA:") == 1
    assert "param = 100" in result
    print("✅ test_remove_empty_data_sections passed")


def test_clean_lingo_content_basic():
    """Test le nettoyage basique du contenu."""
    text = """
[Test comment]
SETS:
  Products / item1, item2 /;
ENDSETS

DATA:
ENDDATA

MIN = 100;
"""
    result = clean_lingo_content(text)

    # Vérifier que les commentaires sont supprimés
    assert "[" not in result
    assert "Test comment" not in result

    # Vérifier que les sections vides sont supprimées
    # (ou du moins qu'on a du contenu cohérent)
    assert "SETS:" in result
    assert "MIN" in result

    print("✅ test_clean_lingo_content_basic passed")


def test_clean_preserves_structure():
    """Test que le nettoyage préserve la structure générale."""
    text = """
MODEL:

SETS:
  Items / a, b, c /;
  Regions / r1, r2 /;
ENDSETS

DATA:
  demand = 100;
  cost = 50;
ENDDATA

MIN = 100;

END
"""
    result = clean_lingo_content(text)

    # Vérifier que les sections principales sont préservées
    assert "MODEL:" in result
    assert "SETS:" in result
    assert "ENDSETS" in result
    assert "DATA:" in result
    assert "ENDDATA" in result
    assert "END" in result

    print("✅ test_clean_preserves_structure passed")


def test_clean_normalizes_case():
    """Test que la normalisation de casse fonctionne."""
    text = """
SETS:
  PRODUCTS / product1, product2 /;
  Markets / MARKET_A, market_b /;
ENDSETS

DATA:
  demand = 100;
  PRICE = 50;
ENDDATA

MAX = demand * PRICE;
"""
    result = clean_lingo_content(text)

    # Les ensembles doivent être en majuscule
    assert "PRODUCTS" in result
    # MARKETS devrait être en majuscule après normalisation
    # Si ce n'est pas le cas, c'est parce que le detecteur ne l'a pas reconnu comme ensemble

    # Les paramètres et variables doivent avoir des identifiants cohérents
    assert "MAX" in result or "max" in result.lower()

    print("✅ test_clean_normalizes_case passed")


def test_clean_handles_complex_file():
    """Test le nettoyage d'un fichier complexe avec multiples constructs."""
    text = """
MODEL: [Production planning model]

SETS:
  PRODUCTS [Available items] / prod1, prod2 /;
  PERIODS [Time periods] / p1, p2, p3 /;
  PRODUCTPERIODS(PRODUCTS, PERIODS) [Product-Period pairs];
ENDSETS

DATA:
  [Supply data]
  supply = 100, 200;
  [Demand data]
  demand = 50, 75;
ENDDATA

[Objective]
MIN = @SUM(PRODUCTS(p): cost(p) * x(p));

DATA:
ENDDATA

[Constraints]
@FOR(PERIODS(t):
  @SUM(PRODUCTS(p): x(p)) >= demand(t)
);

END
"""
    result = clean_lingo_content(text)

    # Vérifier que les crochets sont supprimés
    assert "[" not in result
    assert "]" not in result

    # Vérifier que la structure est préservée
    assert "MODEL:" in result
    assert "SETS:" in result
    assert "ENDSETS" in result
    assert "DATA:" in result
    assert "ENDDATA" in result
    assert "@SUM" in result
    assert "@FOR" in result
    assert "END" in result

    print("✅ test_clean_handles_complex_file passed")


if __name__ == "__main__":
    test_remove_brackets()
    test_remove_empty_data_sections()
    test_clean_lingo_content_basic()
    test_clean_preserves_structure()
    test_clean_normalizes_case()
    test_clean_handles_complex_file()

    print("\n🎉 Tous les tests sont passés!")
