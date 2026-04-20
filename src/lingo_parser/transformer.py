from lark import Transformer, Tree, Token
import sys
import os

src_path = os.path.abspath("../src")
sys.path.append(src_path)

from lingo_parser.parser import *
from lingo_parser.transformer import *

"""
Transformer LINGO → représentation intermédiaire Python.

Ce module contient la classe `LingoModelTransformer2`, un Transformer Lark
chargé de convertir un arbre syntaxique LINGO en une structure Python
exploitable pour la génération automatique de modèles Pyomo.

Le Transformer gère :
- Les ensembles (simples et indexés)
- Les blocs de données
- La fonction objectif (MIN / MAX)
- Les contraintes classiques
- Les boucles @FOR
- Les expressions algébriques (@SUM, @BIN, etc.)

"""


class LingoModelTransformer2(Transformer):
    """
    Transformer Lark pour la conversion de modèles LINGO.

    Cette classe parcourt l'arbre syntaxique produit par Lark
    et construit une représentation intermédiaire du modèle LINGO
    sous forme de dictionnaires Python.

    Cette représentation est ensuite utilisée pour :
    - Générer automatiquement du code Pyomo
    - Produire un notebook Jupyter exécutable
    - Signaler les erreurs ou éléments non traduisibles

    Hérite de :
        lark.Transformer
    """

    # Dictionnaire pour les plages nommées (jours de la semaine, mois, etc.)
    LINGO_RANGES = {
        ("MON", "FRI"): ["MON", "TUE", "WED", "THU", "FRI"],
        ("MON", "SUN"): ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        ("JAN", "DEC"): [
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
        ],
    }

    def model_decl(self, items):
        return {"model": str(items[0])}

    def set_block(self, items):
        sets = []
        for item in items:
            if isinstance(item, dict) and "set_decl" in item:
                sets.append(item["set_decl"])
        return {"sets": sets}

    def set_decl(self, items):
        """
        Traite une déclaration d'ensemble LINGO.

        Supporte :
        - Les ensembles simples avec éléments et attributs
        - Les ensembles indexés (ex: ARC(PRODUCTION, CLIENTS): cost, cap)

        Args:
            items (list): Liste des tokens et sous-arbres produits par Lark.

        Returns:
            dict: Dictionnaire représentant la déclaration de l'ensemble,
            avec son nom, ses indices éventuels, ses éléments et attributs.
        """

        name = str(items[0])

        # Cas avec indices entre parenthèses : ARC(PRODUCTION,CLIENTS):...
        if isinstance(items[1], Token) and items[1].type == "LPAR":
            indices = []
            for it in items[2:]:
                if isinstance(it, Tree) and it.data == "simple_name_list":
                    indices.extend(
                        str(child)
                        for child in it.children
                        if isinstance(child, Token) and child.type in ("NAME", "NUMBER")
                    )
                    break
                if isinstance(it, Token) and it.type == "RPAR":
                    break

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
            has_colon = any(
                isinstance(it, Token) and it.type == "COLON" for it in items
            )
            is_colon_only_decl = (
                len(items) > 1
                and isinstance(items[1], Token)
                and items[1].type == "COLON"
            )

            name_lists = [
                it["name_list"]
                for it in items
                if isinstance(it, dict) and "name_list" in it
            ]

            if len(name_lists) >= 2:
                if len(name_lists) >= 1:
                    elements = name_lists[0]
                if len(name_lists) >= 2:
                    attrs = name_lists[1]
            else:
                if len(name_lists) == 1:
                    if has_colon and is_colon_only_decl:
                        attrs = name_lists[0]
                    else:
                        elements = name_lists[0]

            # Fallback si pas d'attributs détectés
            if not attrs:
                for it in items:
                    if isinstance(it, Token) and it.type in ("NAME", "NUMBER"):
                        s = str(it)
                        if s != name and s not in elements:
                            attrs.append(s)

            return {"set_decl": {"name": name, "elements": elements, "attrs": attrs}}

    def name_list(self, items):
        """Traite une liste de noms, en gérant les plages (NAME..NAME)"""
        result = []
        for item in items:
            if isinstance(item, dict) and "name_range" in item:
                result.extend(item["name_range"])
            elif isinstance(item, Token) and item.type in ("NAME", "NUMBER"):
                result.append(str(item))
        return {"name_list": result}

    def name_range(self, items):
        """
        Traite une plage de noms (NAME..NAME ou NUMBER..NUMBER).

        Supporte :
        - Les plages numériques : 1..5 → ['1', '2', '3', '4', '5']
        - Les plages nommées prédéfinies : MON..FRI → ['MON', 'TUE', 'WED', 'THU', 'FRI']
        - Les éléments simples (sans plage) : NAME → [NAME]

        Note: Lark passe seulement les tokens/enfants, pas les littéraux.
        Pour NAME..NAME, items = [start_token, end_token] (len=2)
        Pour NAME (simple), items = [token] (len=1)
        """
        if len(items) == 1:
            # Pas de plage, juste un élément
            tok = items[0]
            if isinstance(tok, Token):
                return {"name_range": [str(tok)]}
            return {"name_range": []}

        if len(items) == 2:
            # Plage : NAME..NAME ou NUMBER..NUMBER
            start_tok = items[0]
            end_tok = items[1]

            start_str = str(start_tok)
            end_str = str(end_tok)

            # Essayer d'abord dans le dictionnaire prédéfini
            if (start_str, end_str) in self.LINGO_RANGES:
                return {"name_range": self.LINGO_RANGES[(start_str, end_str)]}

            # Essayer comme plage numérique
            try:
                start_num = int(start_str)
                end_num = int(end_str)
                result = [str(i) for i in range(start_num, end_num + 1)]
                return {"name_range": result}
            except ValueError:
                pass

            # Fallback : traiter comme littéral (retourner juste les deux éléments)
            return {"name_range": [start_str, end_str]}

        return {"name_range": []}

    def data_block(self, items):
        """Traite le bloc DATA...ENDDATA du modèle LINGO.

        Parcourt les éléments du bloc DATA et construit un dictionnaire
        ``{nom_attribut: [valeur1, valeur2, ...]}`` listant tous les paramètres
        numériques déclarés.

        Args:
            items (list): Sous-arbres et tokens du bloc DATA.

        Returns:
            dict: ``{"data": {nom: [valeurs]}}`` prêt à fusionner dans le JSON du modèle.
        """
        data = {}
        for item in items:
            if isinstance(item, dict):
                data.update(item)
        return {"data": data}

    def data_stmt(self, items):
        """Traite une instruction DATA du type ``ATTR = v1, v2, ...;``.

        Extrait récursivement toutes les valeurs numériques de l'arbre
        syntaxique associé à l'instruction et les associe au nom de l'attribut.

        Args:
            items (list): ``[nom_token, sous_arbre_valeurs]``.

        Returns:
            dict: ``{nom_attribut: [float, float, ...]}``.
        """
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
        """Traite une étiquette (identifiant) de contrainte LINGO.

        Les étiquettes sont des noms optionnels placés entre crochets avant
        une contrainte (ex: ``[ContrainteProd]``).

        Args:
            items (list): Liste contenant le token du nom de l'étiquette.

        Returns:
            dict: ``{"label": nom_chaine}``.
        """
        return {"label": str(items[0])}

    def objective(self, items):
        """
        Traite la fonction objectif du modèle LINGO.

        Détecte automatiquement :
        - Le sens de l'optimisation (MIN ou MAX)
        - L'expression algébrique associée

        En cas d'absence explicite de direction, MAX est utilisé par défaut.

        Args:
            items (list): Tokens et sous-arbres correspondant à l'objectif.

        Returns:
            dict: Dictionnaire contenant l'objectif sous forme textuelle.
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
        """
        Traite une contrainte du modèle.

        Supporte :
        - Les contraintes algébriques classiques
        - Les contraintes définies via des boucles @FOR

        Args:
            items (list): Éléments syntaxiques composant la contrainte.

        Returns:
            dict: Dictionnaire représentant la contrainte ou la boucle associée.

        Raises:
            ValueError: Si la structure de la contrainte est inattendue.
        """
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
        """Traite une boucle ``@FOR(IndexSet(alias): expr)`` du modèle LINGO.

        Reconstruit la représentation textuelle de la boucle sous la forme
        ``@FOR(IndexSet(alias): expression)`` qui sera ensuite traduite en
        règle Pyomo par le générateur de code.

        Args:
            items (list): Tokens et sous-arbres : ``[FOR, LPAR, indexset, COLON, body, RPAR, SEMICOLON]``.

        Returns:
            dict: ``{"for_loop": "@FOR(...)"}``, ou lève ``ValueError`` si la structure
                est inattendue.

        Raises:
            ValueError: Si l'indexset ou le corps de la boucle est manquant.
        """
        # items contient : FOR, LPAR, indexset, COLON, for_loop_body, RPAR, SEMICOLON
        indexset = None
        expr = None

        for it in items:
            if isinstance(it, Tree) and it.data in (
                "indexset",
                "indexed_set",
                "indexed_set2",
            ):
                indexset = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
                "for_loop_inner",
                "nested_for",
                "cond_nested_for",
            ):
                expr = it
            elif isinstance(it, Tree) and it.data == "for_loop_body":
                expr = it.children[0] if it.children else None
            elif isinstance(it, Tree) and it.data == "bin_expr":
                expr = it

        if indexset is None or expr is None:
            raise ValueError(f"for_loop: structure inattendue: {items}")

        idx_str = self._expr_to_str(indexset)
        expr_str = self._expr_to_str(expr)
        return {"for_loop": f"@FOR({idx_str}: {expr_str})"}

    def nested_for(self, items):
        """Traite un @FOR imbriqué dans le corps d'un autre @FOR."""
        indexset = None
        body = None
        for it in items:
            if isinstance(it, Tree) and it.data in (
                "indexset",
                "indexed_set",
                "indexed_set2",
            ):
                indexset = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
                "nested_for",
                "cond_nested_for",
                "for_loop_body",
            ):
                body = it
        if indexset is None or body is None:
            raise ValueError(f"nested_for: structure inattendue: {items}")
        return Tree("nested_for", [indexset, body])

    def cond_nested_for(self, items):
        """Traite un @FOR conditionnel imbriqué dans le corps d'un autre @FOR."""
        indexset = None
        cond = None
        body = None
        for it in items:
            if isinstance(it, Tree) and it.data in (
                "indexset",
                "indexed_set",
                "indexed_set2",
            ):
                indexset = it
            elif isinstance(it, Tree) and it.data == "cond_filter":
                cond = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
                "nested_for",
                "cond_nested_for",
                "for_loop_body",
            ):
                body = it
        if indexset is None or body is None:
            raise ValueError(f"cond_nested_for: structure inattendue: {items}")
        return Tree("cond_nested_for", [indexset, cond, body])

    def _cond_filter_to_str(self, tree):
        """Convertit un Tree cond_filter en chaîne LINGO 'p#GE#3' ou composée 'f#GE#h-1 #AND# f#LE#h'."""
        if tree is None:
            return ""
        # Nouveau format: un seul Token COND_STR
        if len(tree.children) == 1 and isinstance(tree.children[0], Token):
            return str(tree.children[0])
        # Ancien format de compatibilité: [FILTER_VAR, FILTER_OP, FILTER_VAL]
        var = str(tree.children[0])
        op = str(tree.children[1])
        val = str(tree.children[2])
        return f"{var}{op}{val}"

    def cond_atom_name_offset(self, items):
        """Traite NAME HASH_CMP NAME NUMBER — ex: f#GE#h-1 (le NUMBER est signé, e.g. -1)."""
        var = str(items[0])
        op = str(items[1])
        name = str(items[2])
        offset = str(items[3])  # SIGNED_NUMBER, e.g. "-1" or "+2"
        val = f"{name}{offset}"  # "h-1" ou "h+2"
        return Tree(
            "cond_atom",
            [
                Token("FILTER_VAR", var),
                Token("FILTER_OP", op),
                Token("FILTER_VAL", val),
            ],
        )

    def cond_atom_number(self, items):
        """Traite NAME HASH_CMP NUMBER — ex: p#GE#3."""
        var = str(items[0])
        op = str(items[1])
        val = str(items[2])
        return Tree(
            "cond_atom",
            [
                Token("FILTER_VAR", var),
                Token("FILTER_OP", op),
                Token("FILTER_VAL", val),
            ],
        )

    def cond_atom_name(self, items):
        """Traite NAME HASH_CMP NAME — ex: f#LE#h."""
        var = str(items[0])
        op = str(items[1])
        val = str(items[2])
        return Tree(
            "cond_atom",
            [
                Token("FILTER_VAR", var),
                Token("FILTER_OP", op),
                Token("FILTER_VAL", val),
            ],
        )

    def cond_atom_expr(self, items):
        """Traite expr HASH_CMP expr — ex: k+j #GT# m."""
        left = self._expr_to_str(items[0])
        op = str(items[1])
        right = self._expr_to_str(items[2])
        return Tree(
            "cond_atom",
            [
                Token("FILTER_VAR", left),
                Token("FILTER_OP", op),
                Token("FILTER_VAL", right),
            ],
        )

    def cond_filter(self, items):
        """Traite une condition simple ou composée: 'p#GE#3' ou 'f#GE#h-1 #AND# f#LE#h'."""
        parts = []
        for item in items:
            if isinstance(item, Tree) and item.data == "cond_atom":
                var = str(item.children[0])
                op = str(item.children[1])
                val = str(item.children[2])
                parts.append(f"{var}{op}{val}")
            elif isinstance(item, Token) and item.type == "HASH_BOOL":
                parts.append(str(item))  # e.g. "#AND#"
        cond_str = " ".join(parts)
        return Tree("cond_filter", [Token("COND_STR", cond_str)])

    def cond_for_loop(self, items):
        """Traite @FOR(indexset | condition: body) -> cond_for_loop."""
        indexset = None
        cond = None
        expr = None

        for it in items:
            if isinstance(it, Tree) and it.data in (
                "indexset",
                "indexed_set",
                "indexed_set2",
            ):
                indexset = it
            elif isinstance(it, Tree) and it.data == "cond_filter":
                cond = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
                "for_loop_inner",
                "nested_for",
                "cond_nested_for",
            ):
                expr = it
            elif isinstance(it, Tree) and it.data == "for_loop_body":
                expr = it.children[0] if it.children else None

        if indexset is None or expr is None:
            raise ValueError(f"cond_for_loop: structure inattendue: {items}")

        idx_str = self._expr_to_str(indexset)
        expr_str = self._expr_to_str(expr)
        cond_str = self._cond_filter_to_str(cond) if cond else ""
        if cond_str:
            return {"for_loop": f"@FOR({idx_str} | {cond_str}: {expr_str})"}
        return {"for_loop": f"@FOR({idx_str}: {expr_str})"}

    def for_loop_inner(self, items):
        indexset = None
        expr = None

        for it in items:
            if isinstance(it, Tree) and it.data in (
                "indexset",
                "indexed_set",
                "indexed_set2",
            ):
                indexset = it
            elif isinstance(it, Tree) and it.data in (
                "expr_with_comp",
                "expr",
                "bin_expr",
                "for_loop_inner",
            ):
                expr = it
            elif isinstance(it, Tree) and it.data == "for_loop_body":
                expr = it.children[0] if it.children else None

        if indexset is None or expr is None:
            raise ValueError(f"for_loop_inner: structure inattendue: {items}")

        return Tree("for_loop_inner", [indexset, expr])

    def comp_op(self, items):
        if not items:
            raise ValueError("comp_op: aucun élément trouvé (items est vide)")
        return str(items[0])

    def expr_with_comp(self, items):
        if len(items) != 3:
            raise ValueError(f"expr_with_comp mal formée: {items}")
        return Tree("expr_with_comp", items)

    def index_value(self, items):
        if len(items) != 1:
            raise ValueError(f"index_value mal formé: {items}")
        return items[0]

    def param_ref_arith(self, items):
        """Traite NAME LPAR NAME NUMBER RPAR — ex: Stock_ble(p-1).
        Produit un Tree param_ref avec un Token ARITH_INDEX 'p-1'."""
        tokens = [
            t for t in items if isinstance(t, Token) and t.type not in ("LPAR", "RPAR")
        ]
        # tokens: [NAME(varname), NAME(indexname), NUMBER(offset)]
        # e.g. ['Stock_ble', 'i', '-1']
        if len(tokens) < 3:
            raise ValueError(f"param_ref_arith mal formé: {items}")
        var_token = tokens[0]
        arith_str = "".join(str(t) for t in tokens[1:])  # 'i' + '-1' = 'i-1'
        return Tree("param_ref", [var_token, Token("ARITH_INDEX", arith_str)])

    def index_arith(self, items):
        """Traite NAME NUMBER (ex: p-1) → Token ARITH_INDEX avec valeur 'p-1'."""
        return Token(
            "ARITH_INDEX", "".join(str(t) for t in items if isinstance(t, Token))
        )

    def index_item(self, items):
        """Passe-le-token pour les items d'index simples (NAME ou NUMBER seuls)."""
        return items[0]

    def param_ref(self, items):
        parts = []
        for tok in items:
            if isinstance(tok, Token) and tok.type in ("NAME", "NUMBER", "ARITH_INDEX"):
                parts.append(tok)
            elif isinstance(tok, Tree) and tok.data == "simple_name_list":
                for child in tok.children:
                    if isinstance(child, Token) and child.type in (
                        "NAME",
                        "NUMBER",
                        "ARITH_INDEX",
                    ):
                        parts.append(child)
        if len(parts) < 2:
            raise ValueError(f"param_ref mal formé: {items}")
        return Tree("param_ref", parts)

    def param_ref2(self, items):
        parts = []
        for tok in items:
            if isinstance(tok, Token) and tok.type in ("NAME", "NUMBER", "ARITH_INDEX"):
                parts.append(tok)
            elif isinstance(tok, Tree) and tok.data == "simple_name_list":
                for child in tok.children:
                    if isinstance(child, Token) and child.type in (
                        "NAME",
                        "NUMBER",
                        "ARITH_INDEX",
                    ):
                        parts.append(child)
        if len(parts) < 3:
            raise ValueError(f"param_ref2 mal formé: {items}")
        return Tree("param_ref2", parts)

    def indexed_set(self, items):
        """Extrait le nom du set et ses alias depuis NAME LPAR simple_name_list RPAR."""
        names = []
        for tok in items:
            if isinstance(tok, Token) and tok.type == "NAME":
                names.append(tok)
            elif isinstance(tok, Tree) and tok.data == "simple_name_list":
                for child in tok.children:
                    if isinstance(child, Token) and child.type == "NAME":
                        names.append(child)
        # names[0] = setname, names[1:] = alias(es)
        if len(names) < 2:
            raise ValueError(f"indexed_set mal formé: {items}")
        return Tree("indexed_set", names)

    def indexed_set2(self, items):
        """Extrait le nom du set et ses alias depuis NAME LPAR simple_name_list RPAR (3 noms)."""
        names = []
        for tok in items:
            if isinstance(tok, Token) and tok.type == "NAME":
                names.append(tok)
            elif isinstance(tok, Tree) and tok.data == "simple_name_list":
                for child in tok.children:
                    if isinstance(child, Token) and child.type == "NAME":
                        names.append(child)
        if len(names) < 3:
            raise ValueError(f"indexed_set2 mal formé: {items}")
        return Tree("indexed_set2", names)

    def statement(self, items):
        """Décapsule le contenu du statement"""
        return items[0]

    # --------------- Expression Formatting ----------------
    def _expr_to_str(self, tree):
        """
        Convertit récursivement une expression LINGO en chaîne de caractères.

        Cette méthode est utilisée pour reconstruire des expressions algébriques
        à partir de l'arbre syntaxique Lark (sommes, binaires, références indexées).

        Args:
            tree (Tree | Token): Nœud de l'arbre syntaxique Lark.

        Returns:
            str: Expression LINGO reconstruite sous forme de chaîne.
        """
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
                raise ValueError(
                    f"indexed_set nécessite au moins 2 enfants: {tree.children}"
                )
            name = self._expr_to_str(tree.children[0])
            aliases = ",".join(self._expr_to_str(c) for c in tree.children[1:])
            return f"{name}({aliases})"

        if tree.data == "param_ref":
            if len(tree.children) < 2:
                raise ValueError(
                    f"param_ref nécessite au moins 2 enfants: {tree.children}"
                )
            name = self._expr_to_str(tree.children[0])
            indices = ",".join(self._expr_to_str(c) for c in tree.children[1:])
            return f"{name}({indices})"

        if tree.data == "param_ref2":
            if len(tree.children) < 3:
                raise ValueError(
                    f"param_ref2 nécessite au moins 3 enfants: {tree.children}"
                )
            name = self._expr_to_str(tree.children[0])
            indices = ",".join(self._expr_to_str(c) for c in tree.children[1:])
            return f"{name}({indices})"

        if tree.data == "for_loop_inner":
            if len(tree.children) < 2:
                raise ValueError(f"for_loop_inner nécessite 2 enfants: {tree.children}")
            idx_str = self._expr_to_str(tree.children[0])
            expr_str = self._expr_to_str(tree.children[1])
            return f"@FOR({idx_str}: {expr_str})"

        if tree.data == "nested_for":
            # children: [indexset, body]
            idx_str = self._expr_to_str(tree.children[0])
            body_str = self._expr_to_str(tree.children[1])
            return f"@FOR({idx_str}: {body_str})"

        if tree.data == "cond_nested_for":
            # children: [indexset, cond_filter, body]
            idx_str = self._expr_to_str(tree.children[0])
            cond_str = (
                self._cond_filter_to_str(tree.children[1])
                if len(tree.children) > 2
                else ""
            )
            body_str = self._expr_to_str(
                tree.children[2] if len(tree.children) > 2 else tree.children[1]
            )
            if cond_str:
                return f"@FOR({idx_str} | {cond_str}: {body_str})"
            return f"@FOR({idx_str}: {body_str})"

        if tree.data == "indexed_set2":
            children = [
                c for c in tree.children if isinstance(c, Token) and c.type == "NAME"
            ]
            if len(children) < 3:
                raise ValueError(f"indexed_set2 mal formé: {tree.children}")
            name = str(children[0])
            aliases = ",".join(str(c) for c in children[1:])
            return f"{name}({aliases})"

        if tree.data == "bin_expr":
            # exemple: @BIN(x)
            # children: [BIN token, LPAR token, expr tree, RPAR token]
            inner = self._expr_to_str(tree.children[2])
            return f"@BIN({inner})"

        if tree.data == "sum_expr" and any(
            isinstance(c, Token) and c.value == "@SUM" for c in tree.children
        ):
            idx = next(
                (
                    c
                    for c in tree.children
                    if isinstance(c, Tree)
                    and c.data in ("indexset", "indexed_set", "indexed_set2")
                ),
                None,
            )
            expr = next(
                (c for c in tree.children if isinstance(c, Tree) and c.data == "expr"),
                None,
            )
            return f"@SUM({self._expr_to_str(idx)}: {self._expr_to_str(expr)})"

        if tree.data == "cond_sum_expr":
            idx = next(
                (
                    c
                    for c in tree.children
                    if isinstance(c, Tree)
                    and c.data in ("indexset", "indexed_set", "indexed_set2")
                ),
                None,
            )
            cond = next(
                (
                    c
                    for c in tree.children
                    if isinstance(c, Tree) and c.data == "cond_filter"
                ),
                None,
            )
            inner_expr = next(
                (c for c in tree.children if isinstance(c, Tree) and c.data == "expr"),
                None,
            )
            cond_str = self._cond_filter_to_str(cond) if cond else ""
            if cond_str:
                return f"@SUM({self._expr_to_str(idx)} | {cond_str}: {self._expr_to_str(inner_expr)})"
            return f"@SUM({self._expr_to_str(idx)}: {self._expr_to_str(inner_expr)})"

        parts = [self._expr_to_str(c) for c in tree.children]
        return " ".join(parts)

    def start(self, items):
        """
        Point d'entrée du Transformer.

        Agrège l'ensemble des éléments du modèle LINGO :
        - Ensembles
        - Données
        - Objectif
        - Contraintes
        - Boucles @FOR

        Args:
            items (list): Liste des éléments transformés du modèle.

        Returns:
            dict: Représentation complète du modèle LINGO.
        """
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
