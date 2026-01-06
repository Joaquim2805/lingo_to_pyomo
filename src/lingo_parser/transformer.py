from lark import Transformer, Tree, Token
import sys
import os

src_path = os.path.abspath("../src")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *
from lingo_parser.json_parser import *


class LingoModelTransformer2(Transformer):
    def model_decl(self, items):
        return {"model": str(items[0])}

    def set_block(self, items):
        sets = []
        for item in items:
            if isinstance(item, dict) and "set_decl" in item:
                sets.append(item["set_decl"])
        return {"sets": sets}

    def set_decl(self, items):
        name = str(items[0])

        # Cas avec indices entre parenthèses : ARC(PRODUCTION,CLIENTS):...
        if isinstance(items[1], Token) and items[1].type == "LPAR":
            # Indices
            indices = []
            i = 2
            while i < len(items):
                if isinstance(items[i], Token) and items[i].type == "NAME":
                    indices.append(str(items[i]))
                elif isinstance(items[i], Token) and items[i].type == "RPAR":
                    break
                i += 1

            # Attributs (après ":")
            attrs = []
            found_colon = False
            for it in items:
                if isinstance(it, Token) and it.type == "COLON":
                    found_colon = True
                    continue
                if found_colon:
                    if isinstance(it, dict) and "name_list" in it:
                        attrs.extend(it["name_list"])
                    elif isinstance(it, Token) and it.type == "NAME":
                        attrs.append(str(it))
                    elif isinstance(it, Token) and it.type == "COMMA":
                        continue
                    elif isinstance(it, Token) and it.type == "SEMICOLON":
                        break

            return {"set_decl": {"name": name, "indices": indices, "attrs": attrs}}

        # Cas classique avec slashs
        else:
            elements = []
            attrs = []

            for it in items:
                if isinstance(it, dict) and "name_list" in it:
                    if not elements:
                        elements = it["name_list"]
                    else:
                        attrs = it["name_list"]

            # Fallback si pas d'attributs détectés
            if not attrs:
                for it in items:
                    if isinstance(it, Token) and it.type in ("NAME", "NUMBER"):
                        s = str(it)
                        if s != name and s not in elements:
                            attrs.append(s)

            return {"set_decl": {"name": name, "elements": elements, "attrs": attrs}}

    def name_list(self, items):
        return {
            "name_list": [
                str(tok)
                for tok in items
                if isinstance(tok, Token) and tok.type in ("NAME", "NUMBER")
            ]
        }

    def data_block(self, items):
        data = {}
        for item in items:
            if isinstance(item, dict):
                data.update(item)
        return {"data": data}

    def data_stmt(self, items):
        key = str(items[0])

        def flatten(tree):
            vals = []
            if isinstance(tree, Token) and tree.type == "NUMBER":
                vals.append(float(tree))
            elif isinstance(tree, Tree):
                for c in tree.children:
                    vals.extend(flatten(c))
            return vals

        values = flatten(items[1])
        return {key: values}

    def label(self, items):
        return {"label": str(items[0])}

    def objective(self, items):
        """
        items peut contenir éventuellement un token MIN ou MAX, un token '=',
        et un Tree(expr). On accepte MIN ou MAX (quel que soit la casse).
        Retourne {"objective": "MAX = <expr>"} ou {"objective": "MIN = <expr>"}.
        """
        # Détecter MIN ou MAX (s'il est présent)
        dir_tok = None
        for it in items:
            if isinstance(it, Token):
                v = str(it).upper()
                if v in ("MAX", "MIN"):
                    dir_tok = v
                    break
        if dir_tok is None:
            # fallback : par défaut MAX (ou on pourrait choisir MIN si tu préfères)
            dir_tok = "MAX"

        # Chercher l'arbre d'expression
        expr_tree = next((x for x in items if isinstance(x, Tree)), None)

        if expr_tree is not None:
            expr_str = self._expr_to_str(expr_tree)
        else:
            # fallback : reconstruire une expression simple à partir des tokens non-dir/
            toks = []
            for it in items:
                if isinstance(it, Token):
                    s = str(it)
                    if s.upper() in ("MAX", "MIN", "=", ";"):
                        continue
                    toks.append(s)
                else:
                    toks.append(str(it))
            expr_str = " ".join(toks).strip()
            if not expr_str:
                expr_str = "0"  # si vraiment rien, éviter None

        return {"objective": f"{dir_tok} = {expr_str}"}

    def constraint(self, items):
        # items = [expr, comp_op, expr, (optional SEMICOLON)]
        # Filtrer les tokens SEMICOLON
        filtered = [
            item
            for item in items
            if not (isinstance(item, Token) and item.type == "SEMICOLON")
        ]

        if len(filtered) == 3:
            left, op, right = filtered
            left_s = self._expr_to_str(left)
            op_s = str(op)
            right_s = self._expr_to_str(right)
            return {"constraint": f"{left_s} {op_s} {right_s}"}

        # Sinon cas for_loop ou autre
        if (
            len(filtered) == 1
            and isinstance(filtered[0], dict)
            and "for_loop" in filtered[0]
        ):
            return filtered[0]

        raise ValueError(f"constraint: structure inattendue: {items}")

    def for_loop(self, items):
        # items contient : FOR, LPAR, indexset, COLON, expression, RPAR, SEMICOLON
        indexset = None
        expr = None

        for it in items:
            if isinstance(it, Tree) and it.data in ("indexset", "indexed_set"):
                indexset = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
            ):
                expr = it
            elif isinstance(it, Tree) and it.data == "bin_expr":
                expr = it

        if indexset is None or expr is None:
            raise ValueError(f"for_loop: structure inattendue: {items}")

        idx_str = self._expr_to_str(indexset)
        expr_str = self._expr_to_str(expr)
        return {"for_loop": f"@FOR({idx_str}: {expr_str})"}

    def comp_op(self, items):
        if not items:
            raise ValueError("comp_op: aucun élément trouvé (items est vide)")
        return str(items[0])

    def expr_with_comp(self, items):
        if len(items) != 3:
            raise ValueError(f"expr_with_comp mal formée: {items}")
        return Tree("expr_with_comp", items)

    def param_ref(self, items):
        return Tree("param_ref", items)

    def param_ref2(self, items):
        names = [tok for tok in items if isinstance(tok, Token) and tok.type == "NAME"]
        if len(names) != 3:
            raise ValueError(f"param_ref2 mal formé: {items}")
        return Tree("param_ref2", names)

    def indexed_set(self, items):
        # Extraire seulement les noms (ignorer les parenthèses)
        names = [tok for tok in items if isinstance(tok, Token) and tok.type == "NAME"]
        if len(names) != 2:
            raise ValueError(f"indexed_set mal formé: {items}")
        return Tree("indexed_set", names)

    def statement(self, items):
        """Décapsule le contenu du statement"""
        return items[0]

    # --------------- Expression Formatting ----------------
    def _expr_to_str(self, tree):
        if isinstance(tree, Token):
            if tree.type in {"PLUS", "MINUS", "TIMES", "DIVIDE", "LE", "GE", "EQ"}:
                return str(tree)
            else:
                return str(tree)
        if not isinstance(tree, Tree):
            return str(tree)

        if tree.data == "expr_with_comp":
            left = self._expr_to_str(tree.children[0])
            op = self._expr_to_str(tree.children[1])
            right = self._expr_to_str(tree.children[2])
            return f"{left} {op} {right}"

        # Modifier cette partie
        if tree.data == "indexed_set":
            if len(tree.children) < 2:
                raise ValueError(f"indexed_set nécessite 2 enfants: {tree.children}")
            name = self._expr_to_str(tree.children[0])
            idx = self._expr_to_str(tree.children[1])
            return f"{name}({idx})"

        if tree.data == "param_ref2":
            if len(tree.children) < 3:
                raise ValueError(f"param_ref2 nécessite 3 enfants: {tree.children}")
            name = self._expr_to_str(tree.children[0])
            i = self._expr_to_str(tree.children[1])
            j = self._expr_to_str(tree.children[2])
            return f"{name}({i},{j})"

        if tree.data == "indexed_set":
            print("DEBUG _expr_to_str indexed_set children:", tree.children)
            children = [
                c for c in tree.children if isinstance(c, Token) and c.type == "NAME"
            ]
            if len(children) != 2:
                raise ValueError(f"indexed_set mal formé: {tree.children}")
            name, idx = children
            return f"{name}({idx})"

        if tree.data == "bin_expr":
            # exemple: @BIN(x)
            inner = self._expr_to_str(
                tree.children[1]
            )  # children: [BIN, LPAR, expr, RPAR]
            return f"@BIN({inner})"

        if tree.data == "sum_expr" and any(
            isinstance(c, Token) and c.value == "@SUM" for c in tree.children
        ):
            idx = next(
                (
                    c
                    for c in tree.children
                    if isinstance(c, Tree) and c.data in ("indexset", "indexed_set")
                ),
                None,
            )
            expr = next(
                (c for c in tree.children if isinstance(c, Tree) and c.data == "expr"),
                None,
            )
            return f"@SUM({self._expr_to_str(idx)}: {self._expr_to_str(expr)})"

        parts = [self._expr_to_str(c) for c in tree.children]
        return " ".join(parts)

    def start(self, items):
        model = {
            "sets": [],
            "data": {},
            "constraints": [],
            "for_loops": [],
            "objective": None,
            "label": None,
        }

        for it in items:
            # Ignorer les éléments non pertinents
            if it is None or isinstance(it, Token):
                continue

            if isinstance(it, dict):
                if "sets" in it:
                    model["sets"] = it["sets"]
                elif "data" in it:
                    model["data"] = it["data"]
                elif "objective" in it:
                    model["objective"] = it["objective"]
                elif "label" in it:
                    model["label"] = it["label"]
                elif "constraint" in it:
                    model["constraints"].append(it["constraint"])
                elif "for_loop" in it:
                    model["for_loops"].append(it["for_loop"])

        return model
