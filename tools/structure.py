import os

# Impostazioni principali
ROOT_DIR = "."  # oppure inserisci un path assoluto
OUTPUT_FILE = "project_structure.md"

# Cartelle da ignorare (puoi aggiungerne altre)
EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", ".idea", ".mypy_cache", ".pytest_cache", "dist", "build"
}

def generate_structure(path, prefix=""):
    lines = []
    entries = sorted(os.listdir(path))
    
    for i, entry in enumerate(entries):
        if entry in EXCLUDE_DIRS or entry.startswith('.'):
            continue
        full_path = os.path.join(path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry}")
        if os.path.isdir(full_path):
            extension = "    " if i == len(entries) - 1 else "│   "
            lines.extend(generate_structure(full_path, prefix + extension))
    return lines

def main():
    lines = [f"# 📂 Project Structure Snapshot\n\nRoot: `{os.path.abspath(ROOT_DIR)}`\n\n```\n."]
    lines.extend(generate_structure(ROOT_DIR))
    lines.append("```")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Snapshot salvato in: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
