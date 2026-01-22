import json
import re
from pyomo.environ import *


import sys
import os

src_path = os.path.abspath("../src")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *

import re


def replace_lingo_calls(expr):
    """
    Remplace les appels LINGO du type f(i) ou f(i,j)
    par des accès Pyomo model.f[i] ou model.f[i,j]
    """

    # f(i,j) → model.f[i,j]
    expr = re.sub(
        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)",
        r"model.\1[\2,\3]",
        expr,
    )

    # f(i) → model.f[i]
    expr = re.sub(
        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)",
        r"model.\1[\2]",
        expr,
    )

    return expr


def translate_sum_to_pyomo(expr, sets, cartesian_sets):
    """
    Traduit une expression LINGO de la forme @SUM(...) en une expression Pyomo.

    Cette fonction prend une expression LINGO qui utilise la syntaxe `@SUM(Set[:alias] : expression)`
    et retourne une chaîne représentant l'équivalent Pyomo, par exemple :
        sum(model.param[i,j] * model.x[i,j] for (i,j) in model.ARC)

    Args:
        expr (str): Expression LINGO complète commençant par '@SUM(...)'.
        sets (dict): Dictionnaire des ensembles 1D {set_name: [elements]}.
        cartesian_sets (dict): Dictionnaire des ensembles cartésiens {set_name: [(idx1, idx2), ...]}.

    Returns:
        str: Une chaîne Pyomo construite du type "sum(... for ... in model.Set)".

    Raises:
        ValueError: Si l'expression n'a pas le format attendu ou si le set référencé est inconnu.
    """

    expr = expr.strip()

    # motif principal : @SUM(SetName(:expr)) ou @SUM(SetName(alias):expr)
    m = re.match(
        r"@SUM\s*\(\s*([A-Za-z_]\w*)(?:\((\w+)\))?\s*:\s*(.+)\)",
        expr,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"Format @SUM non reconnu : {expr}")

    setname = m.group(1)
    alias = m.group(2)
    inner_expr = m.group(3).strip()

    # détection de la dimension (1D, 2D, etc.)
    if setname in cartesian_sets:
        indices = cartesian_sets[setname]
        alias_tuple = "(" + ",".join(i[0].lower() for i in indices) + ")"
        gen_clause = f"for {alias_tuple} in model.{setname}"

        # remplacement des variables par model.xxx[i,j]
        inner_expr = replace_lingo_calls(inner_expr)

    elif setname in sets:
        idx = alias or setname[0].lower()
        gen_clause = f"for {idx} in model.{setname}"

        inner_expr = replace_lingo_calls(inner_expr)

    else:
        raise ValueError(f"Set {setname} inconnu dans @SUM.")

    return f"sum({inner_expr} {gen_clause})"


import re


def translate_for_to_pyomo(expr, sets, cartesian_sets):
    """

    Convertit une boucle LINGO @FOR(...) en une triple (setname, alias, expression Pyomo).

    La fonction identifie la boucle `@FOR(Set(alias): <contrainte>)` ou `@FOR(Set: <contrainte>)`,
    remplace les @SUM imbriqués par des compréhensions `sum(... for ... in model.Set)` et produit 
    une expression prête à être utilisée comme corps d'une contrainte Pyomo.
    
    Gère aussi les directives @BIN() pour déclarer des variables binaires.

    Args:
        expr (str): Chaîne LINGO contenant la construction @FOR(...).
        sets (dict): Dictionnaire des ensembles simples.
        cartesian_sets (dict): Dictionnaire des ensembles cartésiens.

    Returns:
        tuple: (setname (str), alias (str or None), constraint_expr (str)) où `constraint_expr` est
            une expression Pyomo valide (ex. "sum(...) + model.Param[a] <= model.B[b]").

    Raises:
        ValueError: Si la syntaxe @FOR ou @SUM imbriquée n'est pas respectée.
    """

    expr = expr.strip().rstrip(";")

    # 1️⃣ Capture @FOR(SetName(alias): constraint_expr) ou @FOR(SetName: constraint_expr)
    # Essayer d'abord avec alias
    m = re.match(
        r"@FOR\s*\(\s*([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)\s*:\s*(.+)\)",
        expr,
        flags=re.IGNORECASE,
    )
    
    if not m:
        # Essayer sans alias
        m = re.match(
            r"@FOR\s*\(\s*([A-Za-z_]\w*)\s*:\s*(.+)\)",
            expr,
            flags=re.IGNORECASE,
        )
        if not m:
            raise ValueError(f"Format @FOR non reconnu : {expr}")
        
        setname = m.group(1)
        alias = None  # Pas d'alias fourni
        constraint_expr = m.group(2).strip()
    else:
        setname = m.group(1)
        alias = m.group(2)
        constraint_expr = m.group(3).strip()

    # 2️⃣ Remplacer les @SUM imbriqués
    def replace_sum(sum_expr):
        sum_expr = sum_expr.strip()
        # Capture SetName(alias): inner_expr
        m_sum = re.match(
            r"@SUM\s*\(\s*([A-Za-z_]\w*)\s*(?:\(([A-Za-z_]\w*)\))?\s*:\s*(.+)\)",
            sum_expr,
            flags=re.IGNORECASE,
        )
        if not m_sum:
            raise ValueError(f"Format @SUM non reconnu : {sum_expr}")

        sum_set = m_sum.group(1)
        sum_alias = m_sum.group(2) or sum_set[0].lower()
        inner = m_sum.group(3).strip()

        # Remplacer Compo(f,b) -> model.Compo[f,b], X(b) -> model.X[b]
        inner = re.sub(
            r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)",
            r"model.\1[\2,\3]",
            inner,
        )
        inner = re.sub(
            r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)",
            lambda m: f"model.{m.group(1)}[{m.group(2)}]"
            if m.group(2) != alias
            else f"model.{m.group(1)}[{alias}]",
            inner,
        )

        return f"sum({inner} for {sum_alias} in model.{sum_set})"

    # Boucle pour remplacer tous les @SUM dans la contrainte
    while "@SUM" in constraint_expr:
        start = constraint_expr.find("@SUM")
        count = 0
        for i, c in enumerate(constraint_expr[start:], start):
            if c == "(":
                count += 1
            elif c == ")":
                count -= 1
                if count == 0:
                    sum_expr = constraint_expr[start : i + 1]
                    constraint_expr = constraint_expr.replace(
                        sum_expr, replace_sum(sum_expr), 1
                    )
                    break

    # 3️⃣ Remplacer les Param 1D ou Var 1D : Dispo(f) -> model.Dispo[f]
    constraint_expr = re.sub(
        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)", r"model.\1[\2]", constraint_expr
    )

    return setname, alias, constraint_expr


def detect_binary_variables(for_loops):
    """
    Détecte les variables binaires déclarées avec @BIN() dans les boucles @FOR.
    
    Args:
        for_loops (list): Liste des chaînes @FOR.
    
    Returns:
        set: Ensemble des noms de variables binaires détectées.
    """
    binary_vars = set()
    for loop in for_loops:
        # Cherche @BIN(variable_name ...) - capture le premier identifiant après @BIN(
        # Gère les cas : @BIN(x), @BIN(x(i)), @BIN(x ( i )), etc.
        matches = re.findall(r"@BIN\s*\(\s*([A-Za-z_]\w*)", loop, flags=re.IGNORECASE)
        binary_vars.update(matches)
    return binary_vars



def translate_single_sum(sum_expr, outer_alias, sets, cartesian_sets):
    """
    Traduit un @SUM isolé en une expression Pyomo 'sum(...)' adaptée au contexte extérieur.

    Utilisée pour les cas où un @SUM apparaît dans une expression déjà qualifiée par un alias
    extérieur (outer_alias). La fonction remplace les variables par leurs accès Pyomo
    (model.var[idx] ou model.var[outer,inner]) en conservant la structure de la somme.

    Args:
        sum_expr (str): Chaîne correspondant à un '@SUM(Set(alias): inner_expr)'.
        outer_alias (str or None): Alias provenant d'une boucle externe si applicable.
        sets (dict): Dictionnaire des ensembles simples.
        cartesian_sets (dict): Dictionnaire des ensembles cartésiens.

    Returns:
        str: Chaîne Pyomo du type "sum(<inner_expr_converted> for <alias> in model.<Set>)".

    Raises:
        ValueError: Si le format du @SUM n'est pas reconnu.
    """

    sum_expr = sum_expr.strip()

    # Capture SetName et alias
    m = re.match(
        r"@SUM\s*\(\s*([A-Za-z_]\w*)\s*(?:\(([A-Za-z_]\w*)\))?\s*:\s*(.+)\)",
        sum_expr,
        flags=re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"Format @SUM non reconnu : {sum_expr}")

    setname = m.group(1)
    alias = m.group(2) or setname[0].lower()
    inner_expr = m.group(3).strip()

    # Remplacer les variables dans l'expression
    tokens = re.findall(r"\b[A-Za-z_]\w*\b", inner_expr)
    for tok in tokens:
        if tok not in [alias, outer_alias, "sum", "for", "in", "and", "or"]:
            if outer_alias:
                inner_expr = re.sub(
                    rf"\b{tok}\b", f"model.{tok}[{outer_alias},{alias}]", inner_expr
                )
            else:
                inner_expr = re.sub(rf"\b{tok}\b", f"model.{tok}[{alias}]", inner_expr)

    # Générer la clause for
    return f"sum({inner_expr} for {alias} in model.{setname})"


def parse_lingo_json(model_json):
    """Analyse le JSON produit par le parser LINGO et extrait les structures du modèle.

    Lit la structure JSON standardisée (sets, cartesian_sets, params, variables, constraints,
    for_loops, objective) et retourne les objets Python utiles pour la génération Pyomo.

    Args:
        model_json (dict): JSON représentant le modèle LINGO.

    Returns:
        tuple: (sets, cartesian_sets, params, variables, constraints, for_loops, objective, direction)
            - sets (dict): ensembles 1D.
            - cartesian_sets (dict): ensembles cartésiens (indices).
            - params (dict): dictionnaire des paramètres.
            - variables (list): liste des (setname, attr) considérés variables.
            - constraints (list): contraintes textuelles extraites.
            - for_loops (list): boucles @FOR textuelles.
            - objective (str): chaîne de l'objectif tel qu'extrait.
            - direction (str): "maximize" ou "minimize".

    Raises:
        KeyError / TypeError: Si la structure JSON n'est pas conforme au format attendu.
    """

    sets = {}
    cartesian_sets = {}
    params = {}
    variables = []

    for s in model_json["sets"]:
        set_name = s["name"]

        if "elements" in s:  # Ensemble simple
            sets[set_name] = s["elements"]
            for attr in s["attrs"]:
                if attr not in model_json["data"]:
                    variables.append((set_name, attr))
                else:
                    params[(set_name, attr)] = model_json["data"][attr]

        elif "indices" in s:  # Ensemble cartésien
            cartesian_sets[set_name] = s["indices"]
            for attr in s["attrs"]:
                if attr in model_json["data"]:
                    params[(set_name, attr)] = model_json["data"][attr]
                else:
                    variables.append((set_name, attr))

    constraints = model_json.get("constraints", [])
    for_loops = model_json.get("for_loops", [])
    objective = model_json.get("objective", "")

    direction = "maximize" if "MAX" in objective.upper() else "minimize"

    return (
        sets,
        cartesian_sets,
        params,
        variables,
        constraints,
        for_loops,
        objective,
        direction,
    )


def detect_scalar_variables(constraints, objective):
    """
    Détecte les variables scalaires (non indexées) présentes dans contraintes et objectif.

    Parcours textuel simple des contraintes et de l'objectif pour repérer des tokens qui semblent
    être des variables scalaires (c.-à-d. des identifiants qui ne correspondent pas à des
    ensembles/params déjà déclarés).

    Args:
        constraints (list of str): Liste des chaînes représentant les contraintes.
        objective (str): Chaîne représentant l'objectif.

    Returns:
        list: Liste triée des noms de variables scalaires détectées.

    Notes:
        - Méthode basée sur une regex simple : elle peut donner des faux positifs si le texte
        contient des identifiants non liés au modèle.
    """

    all_text = " ".join(constraints + [objective])
    return sorted(
        set(re.findall(r"\b[A-Za-z_]\w*\b", all_text)) - {"MAX", "MIN", "SUM", "FOR"}
    )


def safe_replace_variables(expr, variables):
    """
    Remplace les occurrences de variables par 'model.<var>' dans une expression.

    Effectue une substitution par regex en ne remplaçant que les tokens qui figurent dans la
    liste `variables`, afin d'éviter de transformer des mots-clés ou des noms d'ensembles.

    Args:
        expr (str): Expression textuelle où effectuer les remplacements.
        variables (Iterable[str]): Itérable des noms de variables à remplacer.

    Returns:
        str: Expression avec les occurrences de variables préfixées par 'model.'.

    Exemple:
        safe_replace_variables("x + y <= 10", ["x", "y"]) -> "model.x + model.y <= 10"
    """

    def repl(match):
        var = match.group(0)
        return f"model.{var}" if var in variables else var

    return re.sub(r"\b[A-Za-z_]\w*\b", repl, expr)

import re

def translate_constraint_with_sum(c, sets, cartesian_sets, declared_vars, scalar_vars, declared_params):
    """
    Traduit une contrainte LINGO avec @SUM en Pyomo, en gardant l'opérateur et le côté droit.
    """
    # Recherche de l'opérateur
    m = re.match(r"(.+?)(<=|>=|=)(.+)", c.replace(" ", ""))
    if not m:
        raise ValueError(f"Impossible de détecter l'opérateur dans : {c}")
    lhs, op, rhs = m.group(1), m.group(2), m.group(3)

    # Traduction de la partie LHS
    lhs_pyomo = translate_sum_to_pyomo(lhs, sets, cartesian_sets)

    # Traduction du RHS (variables ou paramètres)
    rhs_pyomo = safe_replace_variables(rhs, set(list(declared_vars) + scalar_vars + list(declared_params)))

    return f"{lhs_pyomo} {op} {rhs_pyomo}"



def generate_pyomo_code(model_json):
    (
        sets,
        cartesian_sets,
        params,
        variables,
        constraints,
        for_loops,
        objective,
        direction,
    ) = parse_lingo_json(model_json)

    """
    Génère le code source Pyomo (string) à partir d'un JSON LINGO parsé.

    Cœur du transformateur : cette fonction orchestre la conversion complète d'un modèle LINGO
    (représenté en JSON) en un script Python Pyomo. Elle compose les déclarations de Set, Param,
    Var, Constraint et Objective, tente une traduction des constructions @SUM/@FOR et place des
    commentaires TODO lorsque la traduction automatique n'est pas fiable.

    Étapes principales :
        1. Parser le JSON et extraire sets, cartesian_sets, params, variables, contraintes, for_loops, objectif.
        2. Générer les déclarations de Set (1D et cartésiens).
        3. Générer les Param (1D et multi-dim) en initialisant les dictionnaires de données si nécessaire.
        4. Déclarer les Var en évitant les collisions de noms (ajout de suffixe _var si besoin).
        5. Détecter et déclarer les variables scalaires.
        6. Traduire les contraintes simples ; commenter celles qui contiennent des constructions LINGO complexes.
        7. Tenter de traduire les boucles @FOR en règles Pyomo (best-effort).
        8. Traduire l'objectif (essentiellement @SUM) ou commenter si échec.
        9. Retourner la chaîne complète du script Pyomo.

    Args:
        model_json (dict): JSON déjà désérialisé décrivant le modèle LINGO.

    Returns:
        str: Code Python (Pyomo) complet prêt à être écrit dans un fichier *.py.

    Raises:
        ValueError: Si des éléments structurels essentiels manquent dans le JSON.
        Exception: Les erreurs internes sont capturées et commentées dans le code de sortie
                plutôt que de faire échouer la génération dans la plupart des cas.
    """

    def add_section(title):
        lines.append("")
        lines.append("#" + "=" * 78)
        lines.append(f"# {title}")
        lines.append("#" + "=" * 78)
        lines.append("")

    lines = []
    lines.append("from pyomo.environ import *\n")
    lines.append("model = ConcreteModel()\n")
    add_section("SETS")


    

    # --- Conversion automatique des types (int ou str)
    def _convert_type(val):
        try:
            return int(val)
        except Exception:
            return str(val)

    # === Déclaration des sets ===
    all_set_names = set()
    for setname, elements in sets.items():
        typed_elems = [_convert_type(e) for e in elements]
        lines.append(f"model.{setname} = Set(initialize={typed_elems})")
        all_set_names.add(setname)

    for name, indices in cartesian_sets.items():
        all_set_names.add(name)
        if len(indices) == 2:
            lines.append(
                f"model.{name} = Set(dimen=2, initialize=[(i,j) for i in model.{indices[0]} for j in model.{indices[1]}])"
            )
        elif len(indices) == 3:
            lines.append(
                f"model.{name} = Set(dimen=3, initialize=[(i,j,k) for i in model.{indices[0]} for j in model.{indices[1]} for k in model.{indices[2]}])"
            )

    # === Paramètres ===
    # === Paramètres ===
    # === PARAMÈTRES ===
    add_section("PARAMETERS")
    declared_params = set()

    for (setname, attr), values in params.items():
        declared_params.add(attr)

        # Param scalaire si setname absent
        if setname not in sets and setname not in cartesian_sets:
            val = float(values[0]) if isinstance(values, list) else float(values)
            lines.append(f"model.{attr} = Param(initialize={val}, within=NonNegativeReals)")

        # Param indexé
        else:
            if isinstance(values, list) and len(values) == 1:
                val = float(values[0])
                lines.append(f"model.{attr} = Param(initialize={val}, within=NonNegativeReals)")
            elif isinstance(values, (int, float)):
                lines.append(f"model.{attr} = Param(initialize={values}, within=NonNegativeReals)")
            else:
                from itertools import product

                if setname in cartesian_sets:
                    idx_sets = cartesian_sets[setname]
                    dims = ", ".join(f"model.{idx}" for idx in idx_sets)

                    # 🔴 CORRECTION CRITIQUE ICI
                    cart_keys = list(product(*(sets[idx] for idx in idx_sets)))
                    typed_keys = [
                        tuple(_convert_type(e) for e in k)
                        for k in cart_keys
                    ]

                    data_dict = {
                        typed_keys[i]: float(values[i])
                        for i in range(len(typed_keys))
                    }

                    lines.append(
                        f"model.{attr} = Param({dims}, initialize={data_dict}, within=NonNegativeReals)"
                    )

                else:
                    dims = f"model.{setname}"
                    typed_keys = [_convert_type(e) for e in sets[setname]]

                    data_dict = {
                        typed_keys[i]: float(values[i])
                        for i in range(len(values))
                    }

                    lines.append(
                        f"model.{attr} = Param({dims}, initialize={data_dict}, within=NonNegativeReals)"
                    )

    for key, val in model_json['data'].items():
        # Si le param n'est pas déjà indexé sur un set
        if key not in declared_params:
            scalar_val = float(val[0]) if isinstance(val, list) else float(val)
            lines.append(f"model.{key} = Param(initialize={scalar_val}, within=NonNegativeReals)")
            declared_params.add(key)  # marque comme param déjà déclaré
    # === VARIABLES ===
    declared_vars = set()
    add_section("VARIABLES")
    
    # Détection des variables binaires
    binary_vars = detect_binary_variables(for_loops)

    for setname, attr in variables:
        # Évite collisions avec Param ou Set
        if attr in declared_params or attr in all_set_names:
            safe_attr = f"{attr}_var"
        else:
            safe_attr = attr
        declared_vars.add(safe_attr)

        if setname in cartesian_sets:
            idx = cartesian_sets[setname]
            dims = ", ".join(f"model.{i}" for i in idx)
        else:
            dims = f"model.{setname}"

        # Utiliser domain=Binary si la variable est binaire
        domain = "Binary" if safe_attr in binary_vars else "NonNegativeReals"
        lines.append(f"model.{safe_attr} = Var({dims}, domain={domain})")

    # === Paramètres scalaires non indexés ===
    


    # === Variables scalaires (détectées dans contraintes / objectif) ===
    # ⚠️ Exclure :
    #   - Param déjà déclarés
    #   - alias de @SUM/@FOR (on suppose qu'ils sont en minuscules dans alias_set)
    scalar_vars = detect_scalar_variables(constraints, objective)
    aliases = set()
    for c in constraints + for_loops:
        aliases.update(re.findall(r"\b([a-z])\b", c))  # simple heuristique pour les alias

    for var in scalar_vars:
        if var not in declared_vars and var not in declared_params and var not in all_set_names and var not in aliases:
            lines.append(f"model.{var} = Var(domain=NonNegativeReals)")


    # === Contraintes ===
    add_section("CONSTRAINTS")


    for i, c in enumerate(constraints):
        if not c:
            continue

        c_upper = c.upper()
        if "@FOR" in c_upper or "@BIN" in c_upper:
            lines.append(f"# Constraint {i} not translated (contains FOR/BIN):")
            lines.append(f"#    Original LINGO: {c}")
            lines.append(f"#    TODO: translate this constraint from LINGO to Pyomo.")
        else:
            try:
                if "@SUM" in c_upper:
                    pyomo_expr = translate_constraint_with_sum(
                        c, sets, cartesian_sets, declared_vars, scalar_vars, declared_params
                    )
                else:
                    pyomo_expr = safe_replace_variables(
                        c, set(list(declared_vars) + scalar_vars + list(declared_params))
                    )
                lines.append(f"model.c{i} = Constraint(expr={pyomo_expr})")
            except Exception as e:
                lines.append(f"# FAILED to translate constraint {i}: {e}")
                lines.append(f"# Original: {c}")




    # === Boucles FOR ===
    # Traitement des @FOR qui ne sont pas @BIN (déjà traitées plus haut)
    for i, f in enumerate(for_loops):
        # Ignorer les directives @BIN qui sont traitées dans les déclarations de variables
        if "@BIN" in f.upper() and "@SUM" not in f.upper():
            lines.append(f"# @BIN directive already handled in variable declarations")
            lines.append(f"# Original: {f}")
            continue
        
        try:
            setname, alias, body = translate_for_to_pyomo(f, sets, cartesian_sets)

            cl_name = f"c_for_{i}"
            lines.append(f"model.{cl_name} = ConstraintList()")
            if alias:
                lines.append(f"for {alias} in model.{setname}:")
                lines.append(f"    model.{cl_name}.add({body})")
            else:
                # Pas d'alias : générer une boucle avec une variable implicite
                idx = setname[0].lower()  # i, a, p, etc.
                lines.append(f"for {idx} in model.{setname}:")
                lines.append(f"    model.{cl_name}.add({body})")

        except Exception as e:
            lines.append(f"# FAILED to translate FOR-loop {i}: {e}")
            lines.append(f"# Original: {f}")



    # === Objectif ===
    add_section("OBJECTIVE")
    # Motif pour détecter SUM/FOR/BIN dans l'objectif
    lingo_pattern = re.compile(r"@(?:SUM|FOR|BIN)\b", flags=re.IGNORECASE)


    if objective and lingo_pattern.search(objective):
        try:
            pyomo_obj = translate_sum_to_pyomo(
                objective.replace("MAX =", "").replace("MIN =", "").strip(),
                sets,
                cartesian_sets,
            )
            lines.append(f"model.obj = Objective(expr={pyomo_obj}, sense={direction})")
        except Exception as e:
            lines.append(f"# Objective translation failed: {e}")
            lines.append(f"# Original LINGO: {objective}")
    else:
        pyomo_obj = safe_replace_variables(
            objective.replace("MAX =", "").replace("MIN =", "").strip(),
            set(list(declared_vars) + scalar_vars + list(declared_params)),
        )
        lines.append(f"model.obj = Objective(expr={pyomo_obj}, sense={direction})")

    return "\n".join(lines)
