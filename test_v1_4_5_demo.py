#!/usr/bin/env python3
"""
Test script per v1.4.5-DEMO - Confronto tempi standard
"""
import sys
import os
sys.path.append('./backend')

from api.database import get_db
from api.routers.standard_time import get_times_comparison
from sqlalchemy.orm import Session

def test_comparison_api():
    """Test della nuova API di confronto tempi standard."""
    print("🧪 Test API Confronto Tempi Standard v1.4.5-DEMO")
    print("=" * 60)
    
    try:
        # Ottieni connessione DB
        db = next(get_db())
        
        # Test con TEST-E2E-001
        part_number = "TEST-E2E-001"
        giorni = 30
        
        print(f"📊 Testando part number: {part_number}")
        print(f"📅 Periodo: ultimi {giorni} giorni")
        print()
        
        # Chiamata API
        result = get_times_comparison(part_number, giorni, db)
        
        # Verifica risultato
        print("✅ API chiamata con successo!")
        print()
        print(f"🏷️  Part Number: {result['part_number']}")
        print(f"📈 ODL totali periodo: {result['odl_totali_periodo']}")
        print(f"⚠️  Dati limitati: {'Sì' if result['dati_limitati_globale'] else 'No'}")
        print(f"📊 Scostamento medio: {result['scostamento_medio_percentuale']}%")
        print()
        
        # Dettaglio fasi
        print("🔍 Dettaglio per fase:")
        for fase, dati in result['fasi'].items():
            print(f"  📝 {fase.upper()}")
            print(f"     • Tempo osservato: {dati['tempo_osservato_minuti']:.1f} min")
            print(f"     • Tempo standard: {dati['tempo_standard_minuti']:.1f} min")
            print(f"     • Delta: {dati['delta_percentuale']:.1f}% ({dati['colore_delta']})")
            print(f"     • Osservazioni: {dati['numero_osservazioni']}")
            print(f"     • Dati limitati: {'Sì' if dati['dati_limitati'] else 'No'}")
            print()
        
        # Test del colore del delta
        print("🎨 Test della logica colore:")
        for fase, dati in result['fasi'].items():
            delta = abs(dati['delta_percentuale'])
            colore_atteso = "rosso" if delta > 20 else "giallo" if delta > 10 else "verde"
            simbolo = "✅" if dati['colore_delta'] == colore_atteso else "❌"
            print(f"   {simbolo} {fase}: {delta:.1f}% → {dati['colore_delta']} (atteso: {colore_atteso})")
        
        print()
        print("🎯 TEST COMPLETATO CON SUCCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRORE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comparison_api()
    sys.exit(0 if success else 1) 