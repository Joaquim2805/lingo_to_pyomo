"""
Nettoyage et normalisation des fichiers LINGO.

Ce module fournit des fonctions pour :
- Enlever les accents
- Enlever les commentaires entre crochets [...]
- Normaliser la casse (ensembles en MAJUSCULE, paramètres/variables avec Première_Lettre)
- Supprimer les sections DATA ENDATA vides
- Assurer la cohérence d'écriture d'un même identifiant
"""

import re
import unicodedata
from pathlib import Path
from typing import Dict, Set, Tuple


def _remove_brackets(text: str) -> str:
    """
    Enlève tous les commentaires entre crochets [...].

    Args:
        text: Contenu du fichier LINGO

    Returns:
        Texte sans commentaires entre crochets
    """
    # Enlever tous les [...] (commentaires LINGO)
    text = re.sub(r"\[.*?\]", "", text, flags=re.DOTALL)
    return text


def _remove_accents(text: str) -> str:
    """
    Enlève tous les accents du texte en normalisant les caractères Unicode.

    Exemples:
        "élève" → "eleve"
        "café" → "cafe"
        "résumé" → "resume"

    Args:
        text: Contenu du fichier LINGO

    Returns:
        Texte sans accents
    """
    # Normaliser en NFD (décomposer les caractères accentués)
    nfd = unicodedata.normalize("NFD", text)

    # Enlever les marques diacritiques (accents)
    without_accents = "".join(
        char
        for char in nfd
        if unicodedata.category(char) != "Mn"  # Mn = Mark, nonspacing
    )

    return without_accents


def _extract_identifiers(text: str) -> Dict[str, Set[str]]:
    """
    Extrait tous les identifiants du fichier et leurs variantes d'écriture.
    Catégorise-les comme ensembles, paramètres ou variables.

    Args:
        text: Contenu du fichier LINGO

    Returns:
        Dict avec clés 'sets', 'params', 'variables' contenant des sets d'identifiants
    """
    identifiers = {"sets": set(), "params": set(), "variables": set()}

    # Pattern pour les ensembles: SET nom / elements /;
    set_pattern = r"\bSET\s+([A-Za-z_][A-Za-z0-9_]*)\s*/"
    for match in re.finditer(set_pattern, text):
        identifiers["sets"].add(match.group(1))

    # Pattern pour les sections SETS...ENDSETS
    sets_section = re.search(r"SETS\s*:(.*?)ENDSETS", text, re.DOTALL | re.IGNORECASE)
    if sets_section:
        content = sets_section.group(1)
        # Chercher tous les noms avant : ou / (ensemble)
        # Format: NAME: attr1, attr2;  ou NAME(index1, index2): attr;
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:(]|;)", content):
            name = match.group(1)
            if name.upper() not in ["SETS", "ENDSETS"]:
                identifiers["sets"].add(name)

    # Pattern pour les paramètres et variables: nom = VAR ...;
    # Dans DATA sections
    data_section = re.search(r"DATA\s*:(.*?)ENDDATA", text, re.DOTALL | re.IGNORECASE)
    if data_section:
        content = data_section.group(1)
        # Variables: name = VAR(...)
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*VAR\s*\(", content):
            identifiers["variables"].add(match.group(1))
        # Paramètres: name = valeur;  (pas VAR)
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!\s*VAR)", content):
            ident = match.group(1)
            if not any(ident.lower() == s.lower() for s in identifiers["sets"]):
                if not any(
                    ident.lower() == v.lower() for v in identifiers["variables"]
                ):
                    identifiers["params"].add(ident)

    # Aussi chercher les variables utilisées dans les expressions
    # Format: nom = VAR(...) mais aussi dans les expressions MAX/MIN
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*VAR\s*\(", text):
        identifiers["variables"].add(match.group(1))

    # Chercher les noms avant le caractère ':' dans les expressions @FOR, @SUM, etc.
    for match in re.finditer(
        r"@(?:SUM|FOR)\s*\([^:]*:([A-Za-z_][A-Za-z0-9_]*)\)", text
    ):
        index = match.group(1)
        # C'est un index donc un ensemble
        identifiers["sets"].add(index)

    return identifiers


def _build_case_map(identifiers: Dict[str, Set[str]]) -> Dict[str, str]:
    """
    Construit une cartographie des identifiants vers leur forme normalisée.

    Règles:
    - Ensembles: TOUT_EN_MAJUSCULE
    - Paramètres/Variables: Premiere_Lettre_Majuscule (PascalCase)
    - Un identifiant est unique (case-insensitive)

    Args:
        identifiers: Dict contenant les ensembles, paramètres et variables

    Returns:
        Dict mappant chaque variante d'écriture à sa forme normalisée
    """
    case_map = {}

    # Traiter les ensembles (MAJUSCULE)
    for ident in identifiers["sets"]:
        normalized = ident.upper()
        # Enregistrer toutes les variantes possibles (peu importe la casse)
        case_map[ident.lower()] = normalized
        case_map[ident.upper()] = normalized
        case_map[ident] = normalized

    # Traiter les paramètres et variables (PascalCase)
    for category in ["params", "variables"]:
        for ident in identifiers[category]:
            normalized = _to_pascal_case(ident)
            # Enregistrer toutes les variantes
            case_map[ident.lower()] = normalized
            case_map[ident.upper()] = normalized
            case_map[ident] = normalized

    return case_map


def _generate_variants(word: str) -> list:
    """
    Génère les variantes possibles d'un mot (lowercase, UPPERCASE, mixed case).
    """
    return [word, word.lower(), word.upper()]


def _to_pascal_case(s: str) -> str:
    """
    Convertit un identifiant en PascalCase (Premiere_Lettre_Majuscule).

    Exemples:
        "myVar" -> "MyVar"
        "MY_VAR" -> "MyVar"
        "my_var" -> "MyVar"
    """
    # Remplacer les underscores et passer en PascalCase
    words = s.split("_")
    return "".join(word.capitalize() for word in words if word)


def _normalize_identifiers(text: str, case_map: Dict[str, str]) -> str:
    """
    Remplace tous les identifiants par leurs formes normalisées.

    Utilise un approche smartre pour éviter les remplacements partiels.

    Args:
        text: Contenu du fichier LINGO
        case_map: Cartographie des variantes vers les formes normalisées

    Returns:
        Texte avec identifiants normalisés
    """
    # Créer des groupes d'identifiants par racine (case-insensitive)
    replacements = {}
    for key, value in case_map.items():
        if key not in replacements or len(key) > len(replacements.get(key, "")):
            replacements[key] = value

    # Trier par longueur décroissante pour éviter les remplacements partiels
    sorted_keys = sorted(replacements.keys(), key=len, reverse=True)

    for key in sorted_keys:
        normalized = replacements[key]

        # Remplacer uniquement les mots entiers avec word boundaries
        # Utiliser un callback pour préserver la casse dans certains contextes
        def replacer(match):
            return normalized

        pattern = r"\b" + re.escape(key) + r"\b"
        text = re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    return text


def _remove_empty_data_sections(text: str) -> str:
    """
    Supprime les sections DATA ENDATA qui sont vides.

    Une section est considérée comme vide si elle ne contient que des espaces
    ou des commentaires.

    Args:
        text: Contenu du fichier LINGO

    Returns:
        Texte sans sections DATA ENDATA vides
    """
    # Pattern pour trouver les sections DATA ENDATA
    pattern = r"DATA\s*:(.*?)ENDDATA"

    def is_empty_data(match):
        content = match.group(1)
        # Enlever les commentaires et espaces
        content_clean = re.sub(r"!.*?$", "", content, flags=re.MULTILINE)
        content_clean = content_clean.strip()
        return len(content_clean) == 0

    # Enlever les sections DATA ENDATA vides
    text = re.sub(
        pattern,
        lambda m: "" if is_empty_data(m) else m.group(0),
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return text


def clean_lingo_file(
    lingo_path: str | Path, output_path: str | Path | None = None
) -> str:
    """
    Nettoie un fichier LINGO en appliquant toutes les opérations de nettoyage.

    Étapes:
    1. Enlever les accents
    2. Enlever les commentaires entre crochets [...]
    3. Normaliser la casse des identifiants
    4. Supprimer les sections DATA ENDATA vides

    Args:
        lingo_path: Chemin du fichier LINGO à nettoyer
        output_path: Chemin de sortie (optionnel, génère _clean.lng si None)

    Returns:
        Chemin du fichier nettoyé
    """
    lingo_path = Path(lingo_path)

    # Lire le fichier
    text = lingo_path.read_text(encoding="utf-8")

    # Étape 1: Enlever les accents
    text = _remove_accents(text)

    # Étape 2: Enlever les commentaires entre crochets
    text = _remove_brackets(text)

    # Étape 2: Extraire et normaliser les identifiants
    identifiers = _extract_identifiers(text)
    case_map = _build_case_map(identifiers)
    text = _normalize_identifiers(text, case_map)

    # Étape 3: Enlever les sections DATA ENDATA vides
    text = _remove_empty_data_sections(text)

    # Nettoyer les espaces inutiles (multiple espaces/newlines)
    text = re.sub(r" +", " ", text)  # Remplacer plusieurs espaces par un
    text = re.sub(r"\n\s*\n", "\n\n", text)  # Remplacer plusieurs newlines par deux

    # Écrire le fichier nettoyé
    if output_path is None:
        output_path = lingo_path.with_name(
            lingo_path.stem + "_clean" + lingo_path.suffix
        )
    output_path = Path(output_path)
    output_path.write_text(text, encoding="utf-8")

    return str(output_path.resolve())


def clean_lingo_content(text: str) -> str:
    """
    Nettoie directement le contenu d'un fichier LINGO (sans fichier).

    Utile pour nettoyer le contenu en mémoire.

    Args:
        text: Contenu du fichier LINGO

    Returns:
        Contenu nettoyé
    """
    # Étape 1: Enlever les accents
    text = _remove_accents(text)

    # Étape 2: Enlever les commentaires entre crochets
    text = _remove_brackets(text)

    # Étape 3: Extraire et normaliser les identifiants
    identifiers = _extract_identifiers(text)
    case_map = _build_case_map(identifiers)
    text = _normalize_identifiers(text, case_map)

    # Étape 4: Enlever les sections DATA ENDATA vides
    text = _remove_empty_data_sections(text)

    # Nettoyer les espaces inutiles
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)

    return text
