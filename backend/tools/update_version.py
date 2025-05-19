#!/usr/bin/env python
"""
Utility per aggiornare la versione del progetto CarbonPilot.
Aggiorna i file necessari con la nuova versione e crea un tag git.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

VERSION = "0.2.1"
DATE = datetime.now().strftime("%d/%m/%Y")

def update_version(commit_message=None):
    """Aggiorna la versione del progetto."""
    
    if not commit_message:
        commit_message = f"v{VERSION}: Refactoring modelli database"
    
    # Esegui git add per tutti i file modificati
    subprocess.run(["git", "add", "."], check=True)
    
    # Commit delle modifiche
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    
    # Crea un tag con la nuova versione
    subprocess.run(["git", "tag", f"v{VERSION}"], check=True)
    
    print(f"✅ Versione aggiornata a v{VERSION}")
    print(f"✅ Tag git 'v{VERSION}' creato")
    print(f"✅ Commit: '{commit_message}'")


def main():
    """Funzione principale."""
    parser = argparse.ArgumentParser(description="Aggiorna la versione del progetto CarbonPilot.")
    parser.add_argument("-m", "--message", help="Messaggio di commit personalizzato")
    args = parser.parse_args()
    
    update_version(args.message)


if __name__ == "__main__":
    main() 