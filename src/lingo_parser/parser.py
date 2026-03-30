from lark import Lark
from pathlib import Path


def parse_lingo_model(
    path_to_file, grammar_path=Path(__file__).resolve().parent / "lingogem.lark"
):
    """Parse un modèle LINGO à l'aide de la grammaire Lark.

    Cette fonction charge une grammaire LINGO, lit un fichier source LINGO,
    puis utilise Lark pour produire un arbre syntaxique (parse tree).

    Args:
        path_to_file (str | Path): Chemin du fichier LINGO (.lng) à parser.
        grammar_path (str | Path, optional): Chemin vers la grammaire Lark
            (fichier .lark). Par défaut `"../src/lingo_parser/lingo.lark"`.

    Returns:
        lark.Tree: L'arbre syntaxique généré par le parseur Lark.

    Raises:
        FileNotFoundError: Si le fichier LINGO ou la grammaire n'existent pas.
        lark.exceptions.LarkError: Si le parseur échoue sur le contenu LINGO.
    """
    grammar = Path(grammar_path).read_text(encoding="utf-8")
    parser = Lark(grammar, start="start", parser="lalr")
    code = Path(path_to_file).read_text(encoding="utf-8")
    tree = parser.parse(code)
    return tree
