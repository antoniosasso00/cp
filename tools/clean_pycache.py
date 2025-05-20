#!/usr/bin/env python
"""
Script per pulire i file .pyc e le cartelle __pycache__ dal progetto.
"""

import os
import sys

def clean_pycache():
    """Rimuove tutti i file .pyc e le cartelle __pycache__."""
    print("🧹 Pulizia cache Python in corso...")
    
    for root, dirs, files in os.walk("."):
        # Rimuovi cartelle __pycache__
        for name in dirs:
            if name == "__pycache__":
                path = os.path.join(root, name)
                try:
                    os.system(f"rm -rf {path}")
                    print(f"✅ Rimosso: {path}")
                except Exception as e:
                    print(f"❌ Errore rimozione {path}: {e}")
        
        # Rimuovi file .pyc
        for name in files:
            if name.endswith(".pyc"):
                path = os.path.join(root, name)
                try:
                    os.remove(path)
                    print(f"✅ Rimosso: {path}")
                except Exception as e:
                    print(f"❌ Errore rimozione {path}: {e}")
    
    print("✨ Pulizia completata!")

if __name__ == "__main__":
    clean_pycache() 