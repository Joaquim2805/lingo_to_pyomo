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


def convert_nested_sums(expr, sets, cartesian_sets):
    """
    Convertit de manière récursive les @SUM imbriquées en sum() Pyomo.
    """
    # Chercher le premier @SUM de l'intérieur (le plus interne)
    # pour traiter de l'intérieur vers l'extérieur
    matches = list(re.finditer(r"@SUM\s*\(", expr, re.IGNORECASE))

    if not matches:
        return expr

    # Traiter le dernier (le plus interne) en premier
    for match in reversed(matches):
        sum_start = match.start()

        # Compter les parenthèses pour trouver la fin
        paren_count = 0
        sum_end = -1
        for i in range(sum_start, len(expr)):
            if expr[i] == "(":
                paren_count += 1
            elif expr[i] == ")":
                paren_count -= 1
                if paren_count == 0:
                    sum_end = i + 1
                    break

        if sum_end == -1:
            continue

        inner_sum = expr[sum_start:sum_end]

        try:
            converted = translate_sum_to_pyomo(inner_sum, sets, cartesian_sets)
            expr = expr[:sum_start] + converted + expr[sum_end:]
            # Après chaque conversion, on réapplique récursivement
            expr = convert_nested_sums(expr, sets, cartesian_sets)
            return expr
        except Exception as e:
            continue

    return expr


def translate_sum_to_pyomo(expr, sets, cartesian_sets):
    """
    Traduit une expression LINGO de la forme @SUM(...) en une expression Pyomo.
    Gère les @SUM imbriquées de manière récursive.
    """

    expr = expr.strip()

    # Extraire les composantes du premier @SUM
    if not expr.upper().startswith("@SUM"):
        raise ValueError(f"Format @SUM non reconnu : {expr}")

    # Trouver la position après @SUM(
    sum_start = expr.upper().find("@SUM")
    paren_start = expr.find("(", sum_start)
    if paren_start == -1:
        raise ValueError(f"Format @SUM non reconnu : {expr}")

    # Trouver le ':' qui sépare le SetName et l'expression
    # en comptant les parenthèses pour ne pas être confus par les indices
    paren_count = 1
    colon_pos = -1
    for i in range(paren_start + 1, len(expr)):
        if expr[i] == "(":
            paren_count += 1
        elif expr[i] == ")":
            paren_count -= 1
            if paren_count == 0:
                # On a atteint la fin du @SUM, pas de colon trouvé
                break
        elif expr[i] == ":" and paren_count == 1:
            # On a trouvé le ':' au niveau du @SUM
            colon_pos = i
            break

    if colon_pos == -1:
        raise ValueError(f"Format @SUM non reconnu (pas de ':') : {expr}")

    # Extraire les parties
    set_part = expr[paren_start + 1 : colon_pos].strip()
    expr_part = expr[colon_pos + 1 :].strip()

    # Enlever la parenthèse fermante finale
    if expr_part.endswith(")"):
        expr_part = expr_part[:-1].strip()

    # Parser le set_part: peut être "NAME" ou "NAME(aliases)"
    # Nettoyer les espaces autour des parenthèses: "arc ( t , j )" -> "arc(t,j)"
    set_part_clean = re.sub(r"\s+\(\s*", "(", set_part)  # Espace avant ( -> (
    set_part_clean = re.sub(r"\s+\)", ")", set_part_clean)  # Espace avant ) -> )

    set_match = re.match(r"([A-Za-z_]\w*)(?:\(([^)]*)\))?", set_part_clean)
    if not set_match:
        raise ValueError(f"Format @SUM non reconnu (set) : {expr}")

    setname = set_match.group(1)
    alias_or_indices_raw = set_match.group(2)

    # Nettoyer les indices/alias
    if alias_or_indices_raw:
        alias_or_indices = alias_or_indices_raw.strip()
    else:
        alias_or_indices = None

    # Traiter les @SUM imbriquées dans expr_part de manière récursive
    inner_expr = convert_nested_sums(expr_part, sets, cartesian_sets)

    # Déterminer si c'est plusieurs indices ou un seul alias
    if alias_or_indices and "," in alias_or_indices:
        # Format: @SUM(ARC(c,j):...)
        indices = tuple(idx.strip() for idx in alias_or_indices.split(","))
        idx_for_gen = ",".join(indices)
    else:
        idx_for_gen = None

    # Chercher le set en respectant la casse (LINGO utilise souvent les minuscules)
    # mais les sets peuvent être stockés en majuscules
    actual_setname = setname
    if setname not in cartesian_sets and setname not in sets:
        # Essayer avec la version en majuscules/minuscules opposée
        for key in list(cartesian_sets.keys()) + list(sets.keys()):
            if key.upper() == setname.upper():
                actual_setname = key
                break

    # Générer la clause for
    if actual_setname in cartesian_sets:
        if idx_for_gen:
            gen_clause = f"for {idx_for_gen} in model.{actual_setname}"
        else:
            indices = cartesian_sets[actual_setname]
            alias_tuple = "(" + ",".join(i[0].lower() for i in indices) + ")"
            gen_clause = f"for {alias_tuple} in model.{actual_setname}"
    elif actual_setname in sets:
        idx = (
            alias_or_indices
            if (alias_or_indices and "," not in alias_or_indices)
            else actual_setname[0].lower()
        )
        gen_clause = f"for {idx} in model.{actual_setname}"
    else:
        raise ValueError(f"Set {setname} inconnu dans @SUM.")

    # Remplacer uniquement les appels de fonctions LINGO, pas les noms seuls
    # f(i,j) ou f(5,5) ou f(i,5) → model.f[i,j] ou model.f[5,5] ou model.f[i,5]
    # Gérer tous les types d'indices (alphabétiques et numériques)
    inner_expr = re.sub(
        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_0-9,\s]+)\s*\)",
        r"model.\1[\2]",
        inner_expr,
    )

    return f"sum({inner_expr} {gen_clause})"


import re


def translate_for_to_pyomo(expr, sets, cartesian_sets):
    """

    Convertit une boucle LINGO @FOR(...) en une triple (setname, alias, expression Pyomo).

    La fonction identifie la boucle `@FOR(Set(alias): <contrainte>)` ou `@FOR(Set: <contrainte>)`,
    remplace les @SUM imbriqués par des compréhensions `sum(... for ... in model.Set)` et produit
    une expression prête à être utilisée comme corps d'une contrainte Pyomo.

    Gère aussi les directives @BIN() pour déclarer des variables binaires.
    Gère maintenant les boucles @FOR imbriquées récursivement.

    Args:
        expr (str): Ch\u00e2ine LINGO contenant la construction @FOR(...).
        sets (dict): Dictionnaire des ensembles simples.
        cartesian_sets (dict): Dictionnaire des ensembles cartésiens.

    Returns:
        tuple: (setname (str), alias (str or None), constraint_expr (str), nested_fors (list)) où `constraint_expr` est
            une expression Pyomo valide et nested_fors est une liste de tuples (setname, alias) pour les boucles imbriquées.

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

    # 1b️⃣ Vérifier s'il y a un @FOR imbriqué
    nested_fors = []
    if "@FOR" in constraint_expr.upper():
        # Traiter récursivement le @FOR imbriqué
        try:
            inner_setname, inner_alias, inner_constraint_expr, inner_nested = (
                translate_for_to_pyomo(constraint_expr, sets, cartesian_sets)
            )
            nested_fors.append((inner_setname, inner_alias))
            nested_fors.extend(inner_nested)
            constraint_expr = inner_constraint_expr
        except Exception as e:
            # Si ça échoue, afficher l'erreur et continuer
            print(f"⚠️ Erreur lors du traitement du @FOR imbriqué: {e}")
            print(f"   Expression: {constraint_expr}")
            import traceback

            traceback.print_exc()

    # 2️⃣ Remplacer les @SUM imbriquées en utilisant convert_nested_sums()
    # qui gère correctement tous les formats de @SUM y compris ceux avec des indices
    # multi-dimensionnels et des espaces supplémentaires
    constraint_expr = convert_nested_sums(constraint_expr, sets, cartesian_sets)

    # 2b️⃣ Remplacer les opérateurs d'égalité LINGO (=) par les opérateurs Pyomo (==)
    # Attention: ne pas remplacer les = dans les autres contextes (ex: := pour affectation)
    # Chercher = qui n'est pas suivi de > ou < ou =
    constraint_expr = re.sub(r"(?<![<>!=])\s*=\s*(?![>=])", " == ", constraint_expr)

    # 3️⃣ Remplacer les Param/Var avec indices : x(e,t) -> model.x[e,t] ou x(5,5) -> model.x[5,5]
    # Gère les indices multiples séparés par des virgules, alphanumériques
    constraint_expr = re.sub(
        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_0-9,\s]+)\s*\)",
        r"model.\1[\2]",
        constraint_expr,
    )

    # Ensuite ajouter model. aux paramètres scalaires qui n'ont pas d'arguments
    # (ex: bigM -> model.bigM)
    from pyomo_generator.json_parser import safe_replace_variables
    # Cette ligne será gérée dans le contexte de generate_pyomo_code
    # où on a la liste complète des paramètres et variables

    return setname, alias, constraint_expr, nested_fors


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


def translate_constraint_with_sum(
    c, sets, cartesian_sets, declared_vars, scalar_vars, declared_params
):
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
    rhs_pyomo = safe_replace_variables(
        rhs, set(list(declared_vars) + scalar_vars + list(declared_params))
    )

    # Convertir = en == pour Pyomo
    if op == "=":
        op = "=="

    return f"{lhs_pyomo} {op} {rhs_pyomo}"


def prepare_pyomo_data_dict(model_json, external_data=False):
    """
    Prépare un dictionnaire contenant toutes les données (sets, params) pour externalisation JSON.

    Args:
        model_json (dict): JSON décrivant le modèle LINGO
        external_data (bool): Si True, retourne les données prêtes pour JSON

    Returns:
        dict: Dictionnaire avec structure {sets: {...}, params: {...}, cartesian_data: {...}}
    """
    (
        sets,
        cartesian_sets,
        params,
        _,
        _,
        _,
        _,
        _,
    ) = parse_lingo_json(model_json)

    data_dict = {"sets": {}, "params": {}, "cartesian_data": {}}

    # Conversion des types
    def _convert_type(val):
        try:
            return int(val)
        except Exception:
            return str(val)

    # Externaliser les sets
    for setname, elements in sets.items():
        data_dict["sets"][setname] = [_convert_type(e) for e in elements]

    # Externaliser les params indexés et scalaires
    for (setname, attr), values in params.items():
        if setname not in sets and setname not in cartesian_sets:
            # Param scalaire
            data_dict["params"][attr] = (
                float(values[0]) if isinstance(values, list) else float(values)
            )
        else:
            # Param indexé
            if isinstance(values, list) and len(values) == 1:
                val = float(values[0])
                data_dict["params"][attr] = val
            elif isinstance(values, (int, float)):
                data_dict["params"][attr] = values
            else:
                from itertools import product

                if setname in cartesian_sets:
                    idx_sets = cartesian_sets[setname]
                    cart_keys = list(product(*(sets[idx] for idx in idx_sets)))
                    typed_keys = [tuple(_convert_type(e) for e in k) for k in cart_keys]
                    data_dict["cartesian_data"][attr] = {
                        str(k): float(values[i]) for i, k in enumerate(typed_keys)
                    }
                else:
                    typed_keys = [_convert_type(e) for e in sets[setname]]
                    data_dict["params"][attr] = {
                        str(typed_keys[i]): float(values[i]) for i in range(len(values))
                    }

    # Params supplémentaires du JSON
    for key, val in model_json["data"].items():
        if key not in data_dict["params"] and key not in [p[1] for p in params.keys()]:
            scalar_val = float(val[0]) if isinstance(val, list) else float(val)
            data_dict["params"][key] = scalar_val

    return data_dict


def save_pyomo_data_to_json(model_json, output_path="./data/pyomo_data.json"):
    """
    Sauvegarde les données du modèle LINGO dans un fichier JSON.

    Args:
        model_json (dict): JSON décrivant le modèle LINGO
        output_path (str): Chemin du fichier JSON à créer (par défaut: ./data/pyomo_data.json)

    Returns:
        str: Chemin du fichier créé
    """
    import json
    from pathlib import Path

    data_dict = prepare_pyomo_data_dict(model_json, external_data=True)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(data_dict, f, indent=2)

    return str(output_file)


def load_pyomo_data(input_path="./data/pyomo_data.json"):
    """
    Charge les donnees JSON et convertit les cles string en types natifs.

    Args:
        input_path (str): Chemin du fichier JSON a lire.

    Returns:
        dict: Donnees converties (sets, params, cartesian_data).
    """
    import json
    import ast
    from pathlib import Path

    input_file = Path(input_path)
    with open(input_file, "r") as f:
        data = json.load(f)

    def _convert_key(key):
        if not isinstance(key, str):
            return key
        if key.startswith("(") and key.endswith(")"):
            try:
                return ast.literal_eval(key)
            except Exception:
                return key
        try:
            return int(key)
        except Exception:
            return key

    # Convertir les dictionnaires de parametres indexes
    params = data.get("params", {})
    for pname, pval in list(params.items()):
        if isinstance(pval, dict):
            params[pname] = {_convert_key(k): v for k, v in pval.items()}

    cartesian = data.get("cartesian_data", {})
    for cname, cval in list(cartesian.items()):
        if isinstance(cval, dict):
            cartesian[cname] = {_convert_key(k): v for k, v in cval.items()}

    data["params"] = params
    data["cartesian_data"] = cartesian
    return data


def generate_pyomo_code(
    model_json, external_data=False, data_filename="./data/pyomo_data.json"
):
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

    # Si external_data=True, ajouter le chargement des données depuis JSON
    if external_data:
        lines.append("from pyomo_generator.json_parser import load_pyomo_data")
        lines.append(f"data = load_pyomo_data('{data_filename}')")
        lines.append("")

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
        if external_data:
            lines.append(f"model.{setname} = Set(initialize=data['sets']['{setname}'])")
        else:
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
            if external_data:
                lines.append(
                    f"model.{attr} = Param(initialize=data['params']['{attr}'], within=NonNegativeReals)"
                )
            else:
                val = float(values[0]) if isinstance(values, list) else float(values)
                lines.append(
                    f"model.{attr} = Param(initialize={val}, within=NonNegativeReals)"
                )

        # Param indexé
        else:
            if isinstance(values, list) and len(values) == 1:
                val = float(values[0])
                if external_data:
                    lines.append(
                        f"model.{attr} = Param(initialize=data['params']['{attr}'], within=NonNegativeReals)"
                    )
                else:
                    lines.append(
                        f"model.{attr} = Param(initialize={val}, within=NonNegativeReals)"
                    )
            elif isinstance(values, (int, float)):
                if external_data:
                    lines.append(
                        f"model.{attr} = Param(initialize=data['params']['{attr}'], within=NonNegativeReals)"
                    )
                else:
                    lines.append(
                        f"model.{attr} = Param(initialize={values}, within=NonNegativeReals)"
                    )
            else:
                from itertools import product

                if setname in cartesian_sets:
                    idx_sets = cartesian_sets[setname]
                    dims = ", ".join(f"model.{idx}" for idx in idx_sets)

                    if external_data:
                        lines.append(
                            f"model.{attr} = Param({dims}, initialize=data['cartesian_data']['{attr}'], within=NonNegativeReals)"
                        )
                    else:
                        # 🔴 CORRECTION CRITIQUE ICI
                        cart_keys = list(product(*(sets[idx] for idx in idx_sets)))
                        typed_keys = [
                            tuple(_convert_type(e) for e in k) for k in cart_keys
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

                    if external_data:
                        lines.append(
                            f"model.{attr} = Param({dims}, initialize=data['params']['{attr}'], within=NonNegativeReals)"
                        )
                    else:
                        typed_keys = [_convert_type(e) for e in sets[setname]]
                        data_dict = {
                            typed_keys[i]: float(values[i]) for i in range(len(values))
                        }
                        lines.append(
                            f"model.{attr} = Param({dims}, initialize={data_dict}, within=NonNegativeReals)"
                        )

    for key, val in model_json["data"].items():
        # Si le param n'est pas déjà indexé sur un set
        if key not in declared_params:
            if external_data:
                lines.append(
                    f"model.{key} = Param(initialize=data['params']['{key}'], within=NonNegativeReals)"
                )
            else:
                scalar_val = float(val[0]) if isinstance(val, list) else float(val)
                lines.append(
                    f"model.{key} = Param(initialize={scalar_val}, within=NonNegativeReals)"
                )
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
        aliases.update(
            re.findall(r"\b([a-z])\b", c)
        )  # simple heuristique pour les alias

    for var in scalar_vars:
        if (
            var not in declared_vars
            and var not in declared_params
            and var not in all_set_names
            and var not in aliases
        ):
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
                        c,
                        sets,
                        cartesian_sets,
                        declared_vars,
                        scalar_vars,
                        declared_params,
                    )
                else:
                    # Convertir d'abord les indices avec parenthèses vers des crochets
                    # x(5,5) -> x[5,5], x(e,t) -> x[e,t]
                    c_processed = re.sub(
                        r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_0-9,\s]+)\s*\)", r"\1[\2]", c
                    )
                    pyomo_expr = safe_replace_variables(
                        c_processed,
                        set(list(declared_vars) + scalar_vars + list(declared_params)),
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
            setname, alias, body, nested_fors = translate_for_to_pyomo(
                f, sets, cartesian_sets
            )

            # Ajouter model. aux paramètres scalaires (ex: bigM -> model.bigM)
            # Mais exclure les alias et les variables dans les clauses "for"
            exclude_from_replace = {alias} if alias else set()
            # Aussi exclure les alias des boucles imbriquées
            for inner_setname, inner_alias in nested_fors:
                if inner_alias:
                    exclude_from_replace.add(inner_alias)
            # Aussi exclure les alias dans les clauses "for" comme "for j in model.JOUETS"
            for_aliases = set(re.findall(r"\bfor\s+([A-Za-z_]\w*)\s+in\s+", body))
            exclude_from_replace.update(for_aliases)

            # Ne remplacer que les noms qui ne sont PAS déjà préfixés par "model."
            def smart_replace(match):
                name = match.group(0)
                if name in exclude_from_replace:
                    return name
                # Vérifier si le nom est déjà préfixé par model.
                start_pos = match.start()
                if start_pos >= 6 and body[start_pos - 6 : start_pos] == "model.":
                    return name
                # Vérifier si c'est un paramètre scalaire ou une variable déclarée
                if name in (list(declared_vars) + scalar_vars + list(declared_params)):
                    return f"model.{name}"
                return name

            body = re.sub(r"\b[A-Za-z_]\w*\b", smart_replace, body)

            cl_name = f"c_for_{i}"
            lines.append(f"model.{cl_name} = ConstraintList()")

            # Générer les boucles imbriquées
            indent = ""
            if alias:
                lines.append(f"for {alias} in model.{setname}:")
                indent = "    "
            else:
                # Pas d'alias : générer une boucle avec une variable implicite
                idx = setname[0].lower()  # i, a, p, etc.
                lines.append(f"for {idx} in model.{setname}:")
                indent = "    "
                exclude_from_replace.add(idx)

            # Ajouter les boucles imbriquées
            for inner_setname, inner_alias in nested_fors:
                if inner_alias:
                    lines.append(f"{indent}for {inner_alias} in model.{inner_setname}:")
                    indent += "    "
                else:
                    inner_idx = inner_setname[0].lower()
                    lines.append(f"{indent}for {inner_idx} in model.{inner_setname}:")
                    indent += "    "
                    exclude_from_replace.add(inner_idx)

            lines.append(f"{indent}model.{cl_name}.add({body})")

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
            # Ajouter model. aux paramètres scalaires et variables non-indexées restants
            for_aliases = set(re.findall(r"\bfor\s+([A-Za-z_]\w*)\s+in\s+", pyomo_obj))
            exclude_from_replace = for_aliases.copy()

            def smart_replace(match):
                name = match.group(0)
                if name in exclude_from_replace:
                    return name
                # Vérifier si le nom est déjà préfixé par model.
                start_pos = match.start()
                if start_pos >= 6 and pyomo_obj[start_pos - 6 : start_pos] == "model.":
                    return name
                # Vérifier si c'est un paramètre scalaire ou une variable déclarée
                if name in (declared_vars | set(scalar_vars) | declared_params):
                    return f"model.{name}"
                return name

            pyomo_obj = re.sub(r"\b[A-Za-z_]\w*\b", smart_replace, pyomo_obj)
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
