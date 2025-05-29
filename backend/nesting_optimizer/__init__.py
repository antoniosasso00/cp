"""
Modulo per l'ottimizzazione automatica del nesting degli ODL nelle autoclavi.

Questo modulo contiene gli algoritmi di ottimizzazione per:
- Nesting automatico su piano singolo
- Nesting automatico su due piani
- Ottimizzazione dell'utilizzo dello spazio
"""

from .auto_nesting import compute_nesting, generate_automatic_nesting

__all__ = ["compute_nesting", "generate_automatic_nesting"] 