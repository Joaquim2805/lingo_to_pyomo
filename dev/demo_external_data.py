#!/usr/bin/env python3
"""
Démonstration : Génération de code Pyomo avec données externalisées

Ce script montre comment :
1. Parser un fichier LINGO
2. Générer du code Pyomo avec données externalisées en JSON
3. Sauvegarder le code et les données séparément
4. Utiliser le code généré avec le fichier JSON

Usage:
    python demo_external_data.py <fichier_lingo>

Exemple:
    python demo_external_data.py ../data/Cardoza.lng
"""

import sys
import json
from pathlib import Path

# Ajouter le chemin src au path Python
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from lingo_parser.parser import parse_lingo_model
from lingo_parser.transformer import LingoModelTransformer2
from pyomo_generator.json_parser import (
    generate_pyomo_code,
    save_pyomo_data_to_json,
    prepare_pyomo_data_dict,
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    lingo_file = Path(sys.argv[1])

    if not lingo_file.exists():
        print(f"❌ Erreur : Fichier '{lingo_file}' non trouvé")
        return

    # Créer le répertoire de sortie
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print(f"📌 GÉNÉRATION AVEC DONNÉES EXTERNALISÉES")
    print(f"📄 Fichier source : {lingo_file}")
    print("=" * 70)

    # Étape 1 : Parser et transformer le modèle LINGO
    print("\n[1/4] Parsing du fichier LINGO...")
    try:
        tree = parse_lingo_model(str(lingo_file))
        model_dict = LingoModelTransformer2().transform(tree)
        print("      ✅ Parsing réussi")
    except Exception as e:
        print(f"      ❌ Erreur de parsing : {e}")
        return

    # Étape 2 : Générer le code Pyomo avec données externalisées
    print("\n[2/4] Génération du code Pyomo...")
    try:
        base_name = lingo_file.stem
        data_filename = f"{base_name}_data.json"

        pyomo_code = generate_pyomo_code(
            model_dict, external_data=True, data_filename=data_filename
        )
        print("      ✅ Code généré avec succès")
    except Exception as e:
        print(f"      ❌ Erreur de génération : {e}")
        return

    # Étape 3 : Sauvegarder les données en JSON
    print("\n[3/4] Sauvegarde des données...")
    try:
        data_file = save_pyomo_data_to_json(
            model_dict, output_path=str(output_dir / data_filename)
        )
        print(f"      ✅ Données sauvegardées : {output_dir.name}/{data_filename}")
    except Exception as e:
        print(f"      ❌ Erreur de sauvegarde des données : {e}")
        return

    # Étape 4 : Sauvegarder le code Pyomo
    print("\n[4/4] Sauvegarde du code Pyomo...")
    try:
        code_file = output_dir / f"{base_name}_model.py"
        with open(code_file, "w") as f:
            f.write(pyomo_code)
        print(f"      ✅ Code sauvegardé : {output_dir.name}/{code_file.name}")
    except Exception as e:
        print(f"      ❌ Erreur de sauvegarde du code : {e}")
        return

    # Résumé et statistiques
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE LA GÉNÉRATION")
    print("=" * 70)

    # Lire les statistiques du JSON
    with open(data_file) as f:
        data_content = json.load(f)

    print(f"\n📋 Structure du modèle:")
    print(f"   Sets       : {len(data_content['sets'])} ensemble(s)")
    print(f"   Params     : {len(data_content['params'])} paramètre(s)")
    print(f"   Cartesian  : {len(data_content['cartesian_data'])} produit(s)")

    total_data_size = len(json.dumps(data_content, indent=2))
    total_code_size = len(pyomo_code)

    print(f"\n💾 Taille des fichiers:")
    print(f"   Code Pyomo : {total_code_size:,} octets")
    print(f"   Données    : {total_data_size:,} octets")
    print(f"   Total      : {total_code_size + total_data_size:,} octets")

    print(f"\n📁 Fichiers créés:")
    print(f"   1. {code_file.relative_to(code_file.parent.parent)}")
    print(f"   2. {data_file}")

    print(f"\n✨ Utilisation du code généré:")
    print(f"""
   import sys
   sys.path.insert(0, '{src_path}')
   
   # Exécuter le code Pyomo
   exec(open('{code_file}').read())
   
   # Le modèle Pyomo est maintenant disponible
   print(model.MACHINES)
    """)

    print("=" * 70)


if __name__ == "__main__":
    main()
