import sys
import os

src_path = os.path.abspath("./src/")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *
from pyomo_generator.json_parser import *
from notebook_generator.notebook_construct import *

from pyomo.opt import SolverFactory
from pyomo.environ import value


def test_fleuriste_exp():
    """Test que le fichier fleuriste_exp.lng est traduit correctement en code Pyomo."""
    
    # Parse le fichier LINGO
    tree = parse_lingo_model("./data/fleuriste_exp.lng")
    model_dict = LingoModelTransformer2().transform(tree)
    
    # Génère le code Pyomo
    pyomo_code = generate_pyomo_code(model_dict)
    
    # Code Pyomo attendu
    expected_pyomo_code = """from pyomo.environ import *

model = ConcreteModel()


#==============================================================================
# SETS
#==============================================================================


#==============================================================================
# PARAMETERS
#==============================================================================


#==============================================================================
# VARIABLES
#==============================================================================

model.X1 = Var(domain=NonNegativeReals)
model.X2 = Var(domain=NonNegativeReals)

#==============================================================================
# CONSTRAINTS
#==============================================================================

model.c0 = Constraint(expr=10 * model.X1 + 10 * model.X2 <= 50)
model.c1 = Constraint(expr=10 * model.X1 + 20 * model.X2 <= 80)
model.c2 = Constraint(expr=20 * model.X1 + 10 * model.X2 <= 80)

#==============================================================================
# OBJECTIVE
#==============================================================================

model.obj = Objective(expr=40 * model.X1 + 50 * model.X2, sense=maximize)
""".strip()
    
    # Compare les résultats
    assert pyomo_code.strip() == expected_pyomo_code, \
        f"Code généré ne correspond pas au code attendu.\n\nGénéré:\n{pyomo_code}\n\nAttendu:\n{expected_pyomo_code}"


def test_california_optimal_value():
    """Test que California.lng traduit et résolu donne une valeur optimale de 17."""
    
    # Parse le fichier LINGO
    tree = parse_lingo_model("./data/California.lng")
    model_dict = LingoModelTransformer2().transform(tree)
    
    # Génère le code Pyomo
    pyomo_code = generate_pyomo_code(model_dict)
    
    # Exécute le code Pyomo (crée le modèle)
    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars['model']
    
    # Résout le modèle avec un solveur (par défaut glpk ou cbc)
    solver = SolverFactory('gurobi')  # ou 'cbc' si glpk n'est pas disponible
    result = solver.solve(model, tee=False)
    
    # Récupère la valeur optimale
    optimal_value = value(model.obj)
    
    # Vérifie que la valeur optimale est 17
    assert optimal_value == 17, \
        f"La valeur optimale devrait être 17, mais elle est {optimal_value}"
    


def test_forets_optimal_value():
    """Test que forets.lng traduit et résolu donne une valeur optimale de 17."""
    
    # Parse le fichier LINGO
    tree = parse_lingo_model("./data/forets.lng")
    model_dict = LingoModelTransformer2().transform(tree)
    
    # Génère le code Pyomo
    pyomo_code = generate_pyomo_code(model_dict)
    
    # Exécute le code Pyomo (crée le modèle)
    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars['model']
    
    # Résout le modèle avec un solveur (par défaut glpk ou cbc)
    solver = SolverFactory('gurobi')  # ou 'cbc' si glpk n'est pas disponible
    result = solver.solve(model, tee=False)
    
    # Récupère la valeur optimale
    optimal_value = value(model.obj)
    
    # Vérifie que la valeur optimale est 17
    assert int(optimal_value) == 22333, \
        f"La valeur optimale devrait être 22333.33, mais elle est {optimal_value}"


def test_windor_optimal_value():
    """Test que WINDOR_NONOLE.lng traduit et résolu donne une valeur optimale de 17."""
    
    # Parse le fichier LINGO
    tree = parse_lingo_model("./data/WINDOR_NONOLE.lng")
    model_dict = LingoModelTransformer2().transform(tree)
    
    # Génère le code Pyomo
    pyomo_code = generate_pyomo_code(model_dict)
    
    # Exécute le code Pyomo (crée le modèle)
    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars['model']
    
    # Résout le modèle avec un solveur (par défaut glpk ou cbc)
    solver = SolverFactory('gurobi')  # ou 'cbc' si glpk n'est pas disponible
    result = solver.solve(model, tee=False)
    
    # Récupère la valeur optimale
    optimal_value = value(model.obj)
    
    # Vérifie que la valeur optimale est 17
    assert (optimal_value) == 36, \
        f"La valeur optimale devrait être 36, mais elle est {optimal_value}"



def test_toysarus_optimal_value():
    """Test que toysarus.lng traduit et résolu donne une valeur optimale de 17."""
    
    # Parse le fichier LINGO
    tree = parse_lingo_model("./data/toysarus.lng")
    model_dict = LingoModelTransformer2().transform(tree)
    
    # Génère le code Pyomo
    pyomo_code = generate_pyomo_code(model_dict)
    
    # Exécute le code Pyomo (crée le modèle)
    local_vars = {}
    exec(pyomo_code, local_vars)
    model = local_vars['model']
    
    # Résout le modèle avec un solveur (par défaut glpk ou cbc)
    solver = SolverFactory('gurobi')  # ou 'cbc' si glpk n'est pas disponible
    result = solver.solve(model, tee=False)
    
    # Récupère la valeur optimale
    optimal_value = value(model.obj)
    
    # Vérifie que la valeur optimale est 17
    assert (optimal_value) == 230000.0, \
        f"La valeur optimale devrait être 23000, mais elle est {optimal_value}"

