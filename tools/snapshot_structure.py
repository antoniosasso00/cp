# tools/snapshot_structure.py

import os

IGNORED_DIRS = {'.git', '.venv', '__pycache__', '.mypy_cache', '.pytest_cache'}
OUTPUT_FILE = "project_structure.md"

def generate_structure(root_dir):
    lines = ["# 🧱 Progetto CarbonPilot – Struttura Corrente\n"]

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filtra cartelle da ignorare
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        depth = dirpath.replace(root_dir, '').count(os.sep)
        indent = "    " * depth
        folder = os.path.basename(dirpath)
        lines.append(f"{indent}📁 {folder}/")

        for filename in sorted(filenames):
            if not filename.startswith('.') and not filename.endswith('.pyc'):
                lines.append(f"{indent}    └── {filename}")

    return "\n".join(lines)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    structure = generate_structure(root_dir)

    with open(os.path.join(root_dir, OUTPUT_FILE), "w", encoding="utf-8") as f:
        f.write(structure)

    print(f"✅ Struttura salvata in: {OUTPUT_FILE}")
