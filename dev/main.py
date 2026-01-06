import sys
import os

src_path = os.path.abspath("../src/")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *


from notebook_generator.notebook_construct import *


def generate_notebook():
    tree = parse_lingo_model("../data/fleuriste_alg.lng")
    model_dict = LingoModelTransformer2().transform(tree)

    pyomo_code = generate_pyomo_code(model_dict)

    generate_pyomo_notebook(pyomo_code, solver="gurobi", filename="fleuriste.ipynb")


from rich.console import Console
from rich.progress import track
import typer

app = typer.Typer()
console = Console()


@app.command()
def main():
    console.print(f"[bold green]Génération du notebook pour :[/]")
    for _ in track(range(100), description="Processing..."):
        pass  # tu peux mettre un vrai traitement ici
    generate_notebook()
    console.print("ok")


if __name__ == "__main__":
    app()
