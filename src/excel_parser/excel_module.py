from pathlib import Path
import re
import pandas as pd
from math import prod


from openpyxl import load_workbook
from openpyxl.cell.cell import Cell


def read_excel_defined_zones(filename):
    """
    Lit les zones nommées définies dans Excel (menu déroulant),
    compatible cellules uniques, lignes, matrices.
    """

    wb = load_workbook(filename, data_only=True)
    zones = []

    for defn in wb.defined_names.values():
        name = defn.name

        for sheet_name, coord in defn.destinations:
            ws = wb[sheet_name]

            area = ws[coord]

            # Cas 1 : cellule unique
            if isinstance(area, Cell):
                values = [[area.value]]

            # Cas 2 : plage (tuple de lignes)
            else:
                values = [[cell.value for cell in row] for row in area]

            df = pd.DataFrame(values)

            zones.append(
                {
                    "name": name,
                    "sheet": sheet_name,
                    "range": coord,
                    "shape": df.shape,
                    "data": df,
                }
            )

    return zones


def _normalize_name(name: str) -> str:
    return str(name).strip().lower()


def _sanitize_elem(value: str) -> str:
    # Supprimer les espaces pour qu'un élément reste un seul token LINGO
    return str(value).strip().replace(" ", "")


def _zone_map_from_excel(excel_path: str) -> dict:
    zones = read_excel_defined_zones(excel_path)
    return {_normalize_name(z["name"]): z["data"] for z in zones}


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all").dropna(axis=1, how="all")


def _format_list(values):
    return ",".join(str(v) for v in values)


def _format_matrix_row_major(df: pd.DataFrame, expected_rows=None, expected_cols=None):
    """Formate une matrice en row-major order en préservant toutes les valeurs."""
    # Ne PAS nettoyer pour les matrices - chaque cellule compte
    actual_rows, actual_cols = df.shape

    if expected_rows is not None and expected_cols is not None:
        if actual_rows != expected_rows or actual_cols != expected_cols:
            print(
                f"⚠️ Avertissement: Dimensions Excel ({actual_rows}×{actual_cols}) != dimensions attendues ({expected_rows}×{expected_cols})"
            )

    # Remplacer NaN par 0 pour les matrices (important pour matrices de connectivité)
    values = df.fillna(0).values.flatten().tolist()
    # Convertir en int si ce sont des entiers
    values = [
        int(v) if isinstance(v, (int, float)) and v == int(v) else v for v in values
    ]
    return ",".join(str(v) for v in values)


def _strip_headers(df: pd.DataFrame, row_labels=None, col_labels=None) -> pd.DataFrame:
    """Supprime les en-têtes de ligne/colonne d'une matrice Excel en préservant toutes les données."""
    # Ne pas nettoyer au début pour ne pas perdre de données
    df2 = df.copy()

    if row_labels:
        row_labels = [_sanitize_elem(v) for v in row_labels]
    if col_labels:
        col_labels = [_sanitize_elem(v) for v in col_labels]

    # Détecter si les dimensions sont inversées dans Excel
    if (
        row_labels is not None
        and col_labels is not None
        and len(df2.index) > 0
        and len(df2.columns) > 0
    ):
        first_row = df2.iloc[0].astype(str).str.strip().tolist()
        first_row = [_sanitize_elem(v) for v in first_row]
        first_col = df2.iloc[:, 0].astype(str).str.strip().tolist()
        first_col = [_sanitize_elem(v) for v in first_col]

        # Ne transposer que si la correspondance est MAJORITAIRE des deux côtés.
        # Avec un simple any(), des valeurs numériques qui se recoupent (ex: 1,2,3)
        # peuvent provoquer une transposition erronée des matrices (cas Omega/HRPROD).
        row_match_ratio = (
            sum(1 for v in first_row if v in row_labels) / len(first_row)
            if len(first_row) > 0
            else 0
        )
        col_match_ratio = (
            sum(1 for v in first_col if v in col_labels) / len(first_col)
            if len(first_col) > 0
            else 0
        )

        # On transpose uniquement si les en-têtes semblent vraiment inversés.
        if row_match_ratio > 0.5 and col_match_ratio > 0.5:
            df2 = df2.T  # Transposer
            first_row = df2.iloc[0].astype(str).str.strip().tolist()
            first_row = [_sanitize_elem(v) for v in first_row]
            first_col = df2.iloc[:, 0].astype(str).str.strip().tolist()
            first_col = [_sanitize_elem(v) for v in first_col]

    # Supprimer la première ligne si elle contient des en-têtes de colonnes
    # CRITÈRE STRICT: La majorité (>50%) des éléments doivent correspondre aux col_labels
    if col_labels is not None and len(df2.index) > 0:
        first_row = df2.iloc[0].astype(str).str.strip().tolist()
        first_row_clean = [_sanitize_elem(v) for v in first_row]
        matches = sum(1 for v in first_row_clean if v in col_labels)
        match_ratio = matches / len(first_row_clean) if len(first_row_clean) > 0 else 0

        # Ligne d'en-tête seulement si >50% des éléments sont dans col_labels
        if match_ratio > 0.5:
            df2 = df2.iloc[1:, :]

    # Supprimer la première colonne si elle contient des en-têtes de lignes
    # CRITÈRE STRICT: La majorité (>50%) des éléments doivent correspondre aux row_labels
    if row_labels is not None and len(df2.columns) > 0:
        first_col = df2.iloc[:, 0].astype(str).str.strip().tolist()
        first_col_clean = [_sanitize_elem(v) for v in first_col]
        matches = sum(1 for v in first_col_clean if v in row_labels)
        match_ratio = matches / len(first_col_clean) if len(first_col_clean) > 0 else 0

        # Colonne d'en-tête seulement si >50% des éléments sont dans row_labels
        if match_ratio > 0.5:
            df2 = df2.iloc[:, 1:]

    # Réinitialiser les index pour avoir des index numériques propres
    df2 = df2.reset_index(drop=True)
    df2.columns = range(len(df2.columns))

    return df2


def _lingo_value_from_zone(
    df: pd.DataFrame,
    row_labels=None,
    col_labels=None,
    expected_rows=None,
    expected_cols=None,
) -> str:
    df = _strip_headers(df, row_labels=row_labels, col_labels=col_labels)
    if df.shape == (1, 1):
        v = df.iat[0, 0]
        return str(v) if pd.notna(v) else ""
    if df.shape[0] == 1 or df.shape[1] == 1:
        vals = [v for v in df.values.flatten().tolist() if pd.notna(v)]
        return _format_list(vals)

    # Si aucune dimension attendue n'est fournie explicitement,
    # on conserve le comportement historique basé sur 2 dimensions.
    if expected_rows is None and expected_cols is None:
        expected_rows = len(row_labels) if row_labels else None
        expected_cols = len(col_labels) if col_labels else None

    return _format_matrix_row_major(df, expected_rows, expected_cols)


def _parse_ole_args(ole_args: str):
    # Retourne (excel_path, range_name_or_none)
    parts = [p.strip() for p in ole_args.split(",")]

    def _strip_quotes(s):
        return s.strip().strip('"').strip("'")

    excel_path = _strip_quotes(parts[0]) if parts else None
    range_name = _strip_quotes(parts[1]) if len(parts) > 1 else None
    return excel_path, range_name


def _inject_set_elements(text: str, zone_map: dict) -> str:
    # Insère les éléments dans SETS si absents: SETNAME: ... -> SETNAME /a,b/ : ...
    m = re.search(r"SETS:(.*?)ENDSETS", text, flags=re.S | re.I)
    if not m:
        return text
    block = m.group(1)
    new_lines = []
    for raw_line in block.splitlines():
        line_part, comment = (raw_line.split("!", 1) + [""])[:2]
        comment = ("!" + comment) if comment != "" else ""
        if "/" not in line_part:
            m2 = re.match(r"(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^;]*);", line_part)
            if m2:
                indent, set_name, tail = m2.groups()
                key = _normalize_name(set_name)
                if key in zone_map:
                    vals = _lingo_value_from_zone(zone_map[key]).split(",")
                    vals = [_sanitize_elem(v) for v in vals if v != ""]
                    line_part = (
                        f"{indent}{set_name} /{_format_list(vals)}/:{tail.strip()};"
                    )
        new_lines.append(line_part + comment)
    new_block = "\n".join(new_lines)
    if block.endswith("\n"):
        new_block += "\n"
    return text[: m.start(1)] + new_block + text[m.end(1) :]


def _parse_sets_and_dims(text: str):
    # Extrait les éléments d'ensembles définis dans SETS et les dimensions des variables
    m = re.search(r"SETS:(.*?)ENDSETS", text, flags=re.S | re.I)
    block = m.group(1) if m else ""
    lines = [ln.split("!")[0].strip() for ln in block.splitlines()]
    block = "\n".join([ln for ln in lines if ln])

    set_elements = {}
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*/([^/]+)/", block):
        set_name = match.group(1)
        elems = [e.strip() for e in match.group(2).split(",") if e.strip()]
        elems = [_sanitize_elem(e) for e in elems]
        set_elements[_normalize_name(set_name)] = elems

    var_dims = {}
    # pattern: SETNAME: v1, v2;
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*:\s*([^;]+);", block):
        set_name = match.group(1)
        vars_part = match.group(2)
        vars_list = [v.strip() for v in vars_part.split(",") if v.strip()]
        for var in vars_list:
            var_dims[_normalize_name(var)] = [_normalize_name(set_name)]

    # pattern: ARC(MAT,PROD): var1, var2;
    for match in re.finditer(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]+)\)\s*:\s*([^;]+);", block
    ):
        dims = [d.strip() for d in match.group(2).split(",") if d.strip()]
        vars_part = match.group(3)
        vars_list = [v.strip() for v in vars_part.split(",") if v.strip()]
        for var in vars_list:
            var_dims[_normalize_name(var)] = [_normalize_name(d) for d in dims]

    return set_elements, var_dims


def _get_dim_labels(var_name: str, set_elements: dict, var_dims: dict):
    dims = var_dims.get(_normalize_name(var_name), [])
    row_labels = set_elements.get(dims[0], None) if len(dims) >= 1 else None
    col_labels = set_elements.get(dims[1], None) if len(dims) >= 2 else None
    return row_labels, col_labels


def _get_expected_matrix_shape(var_name: str, set_elements: dict, var_dims: dict):
    dims = var_dims.get(_normalize_name(var_name), [])
    if len(dims) < 2:
        return None, None

    dim_sizes = [len(set_elements.get(dim, [])) for dim in dims]
    if any(size == 0 for size in dim_sizes):
        return None, None

    # Convention Excel utilisée ici: première dimension en lignes,
    # produit des dimensions restantes en colonnes (aplatissement row-major).
    expected_rows = dim_sizes[0]
    expected_cols = prod(dim_sizes[1:])
    return expected_rows, expected_cols


def _replace_set_ole(text: str, zone_map: dict) -> str:
    # Remplace SETNAME /@OLE('file')/ par SETNAME /a,b,c/ (zone = SETNAME)
    pattern = re.compile(r"(\b([A-Za-z_][A-Za-z0-9_]*)\b\s*/)(\s*@OLE\(([^)]*)\)\s*/)")

    def repl(match):
        set_name = match.group(2)
        key = _normalize_name(set_name)
        if key not in zone_map:
            return match.group(0)
        vals = _lingo_value_from_zone(zone_map[key]).split(",")
        vals = [_sanitize_elem(v) for v in vals if v != ""]
        return f"{set_name} /{_format_list(vals)}/"

    return pattern.sub(repl, text)


def _replace_data_ole(
    text: str, zone_map: dict, set_elements: dict, var_dims: dict
) -> str:
    # Remplace les assignations DATA ... = @OLE(...)
    # Cas multi-variables: a, b, c = @OLE('file');
    multi_pattern = re.compile(
        r"^\s*([A-Za-z0-9_\s,]+)\s*=\s*@OLE\(([^)]*)\)\s*;\s*$", re.MULTILINE
    )

    def multi_repl(match):
        left = match.group(1)
        ole_args = match.group(2)
        _, range_name = _parse_ole_args(ole_args)
        vars_list = [v.strip() for v in left.split(",") if v.strip()]
        lines = []
        for var in vars_list:
            if _normalize_name(var) in set_elements:
                # Les ensembles sont définis dans SETS, pas dans DATA
                continue
            key = _normalize_name(range_name or var)
            if key not in zone_map:
                raise KeyError(f"Zone '{range_name or var}' introuvable pour {var}")
            row_labels, col_labels = _get_dim_labels(var, set_elements, var_dims)
            expected_rows, expected_cols = _get_expected_matrix_shape(
                var, set_elements, var_dims
            )
            val = _lingo_value_from_zone(
                zone_map[key],
                row_labels=row_labels,
                col_labels=col_labels,
                expected_rows=expected_rows,
                expected_cols=expected_cols,
            )
            lines.append(f"{var} = {val};")
        return "\n".join(lines)

    text = multi_pattern.sub(multi_repl, text)

    # Cas simple: var = @OLE('file','range');
    single_pattern = re.compile(
        r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*@OLE\(([^)]*)\)\s*;\s*$", re.MULTILINE
    )

    def single_repl(match):
        var = match.group(1)
        if _normalize_name(var) in set_elements:
            return ""
        ole_args = match.group(2)
        _, range_name = _parse_ole_args(ole_args)
        key = _normalize_name(range_name or var)
        if key not in zone_map:
            raise KeyError(f"Zone '{range_name or var}' introuvable pour {var}")
        row_labels, col_labels = _get_dim_labels(var, set_elements, var_dims)
        expected_rows, expected_cols = _get_expected_matrix_shape(
            var, set_elements, var_dims
        )
        val = _lingo_value_from_zone(
            zone_map[key],
            row_labels=row_labels,
            col_labels=col_labels,
            expected_rows=expected_rows,
            expected_cols=expected_cols,
        )
        return f"{var} = {val};"

    text = single_pattern.sub(single_repl, text)

    # Supprimer les lignes d'export vers Excel (@OLE(...) = ...;)
    text = re.sub(r"^\s*@OLE\([^)]*\)\s*=.*;\s*$", "", text, flags=re.MULTILINE)
    return text


def _parse_declared_attrs(text: str) -> dict[str, str]:
    m = re.search(r"SETS:(.*?)ENDSETS", text, flags=re.S | re.I)
    block = m.group(1) if m else ""
    attrs_by_norm = {}
    for raw_line in block.splitlines():
        line = raw_line.split("!", 1)[0].strip()
        if not line or ":" not in line or line.endswith(":;"):
            continue
        _, attrs_part = line.split(":", 1)
        attrs_part = attrs_part.rsplit(";", 1)[0]
        for attr in [item.strip() for item in attrs_part.split(",") if item.strip()]:
            attrs_by_norm[_normalize_name(attr)] = attr
    return attrs_by_norm


def _is_likely_parameter_usage(text: str, attr_name: str) -> bool:
    attr_pattern = re.escape(attr_name)
    patterns = [
        rf"\b{attr_pattern}\s*\([^)]*\)\s*[*/]",
        rf"[*/]\s*{attr_pattern}\s*\(",
        rf"(?:<=|>=|=)\s*{attr_pattern}(?:\s*\(|\b)",
    ]
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def _inject_implicit_data_block(
    text: str, zone_map: dict, set_elements: dict, var_dims: dict
) -> str:
    attrs_by_norm = _parse_declared_attrs(text)
    if not attrs_by_norm:
        return text

    inferred_lines = []
    for key, attr_name in attrs_by_norm.items():
        if key not in zone_map:
            continue
        if not _is_likely_parameter_usage(text, attr_name):
            continue

        row_labels, col_labels = _get_dim_labels(attr_name, set_elements, var_dims)
        expected_rows, expected_cols = _get_expected_matrix_shape(
            attr_name, set_elements, var_dims
        )
        value = _lingo_value_from_zone(
            zone_map[key],
            row_labels=row_labels,
            col_labels=col_labels,
            expected_rows=expected_rows,
            expected_cols=expected_cols,
        )
        inferred_lines.append(f"{attr_name} = {value};")

    if not inferred_lines:
        return text

    data_match = re.search(r"DATA:(.*?)ENDDATA", text, flags=re.S | re.I)
    if data_match:
        block = data_match.group(1)
        assigned = {
            _normalize_name(name)
            for name in re.findall(
                r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", block, flags=re.MULTILINE
            )
        }
        if assigned:
            return text
        missing_lines = [
            line
            for line in inferred_lines
            if _normalize_name(line.split("=", 1)[0].strip()) not in assigned
        ]
        if not missing_lines:
            return text
        insertion = "\n" + "\n".join(missing_lines)
        return text[: data_match.end(1)] + insertion + text[data_match.end(1) :]

    endsets_match = re.search(r"ENDSETS", text, flags=re.I)
    if not endsets_match:
        return text

    data_block = "\n\nDATA:\n" + "\n".join(inferred_lines) + "\nENDDATA"
    return text[: endsets_match.end()] + data_block + text[endsets_match.end() :]


def convert_lingo_ole_to_explicit(
    lingo_path: str, output_path: str | None = None, excel_path: str | None = None
) -> str:
    lingo_path = Path(lingo_path)
    text = lingo_path.read_text(encoding="utf-8")

    # Détecter automatiquement le fichier Excel si non fourni
    if excel_path is None:
        m = re.search(r"@OLE\(\s*['\"]([^'\"]+)['\"]", text)
        if not m:
            raise ValueError("Aucun @OLE(...) trouvé pour détecter le fichier Excel")
        excel_path = m.group(1)

    excel_path = str((lingo_path.parent / excel_path).resolve())
    zone_map = _zone_map_from_excel(excel_path)

    # Remplacer d'abord les SETS @OLE, injecter les éléments d'ensemble, puis extraire les ensembles et dimensions
    text = _replace_set_ole(text, zone_map)
    text = _inject_set_elements(text, zone_map)
    set_elements, var_dims = _parse_sets_and_dims(text)

    text = _replace_data_ole(text, zone_map, set_elements, var_dims)
    text = _inject_implicit_data_block(text, zone_map, set_elements, var_dims)

    if output_path is None:
        output_path = lingo_path.with_name(
            lingo_path.stem + "_explicit" + lingo_path.suffix
        )
    output_path = Path(output_path)
    output_path.write_text(text, encoding="utf-8")
    return str(output_path.resolve())
