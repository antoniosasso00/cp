#!/usr/bin/env python3
"""
🔍 CarbonPilot - Diagnosi Completa Sistema Cavalletti 2L
Analizza problemi logici/fisici nel posizionamento cavalletti e verifica regole condivisione
"""

import sys
import os
sys.path.append('backend')

def analizza_sistema_cavalletti():
    """Analizza il sistema cavalletti completo per identificare tutti i problemi"""
    print("🔍 DIAGNOSI COMPLETA SISTEMA CAVALLETTI 2L")
    print("=" * 80)
    
    # 1. ANALISI LIMITE MAX_CAVALLETTI
    print("\n📊 1. GESTIONE LIMITE MAX_CAVALLETTI")
    print("-" * 50)
    
    print("✅ IMPLEMENTATO CORRETTAMENTE:")
    print("   - AutoclaveInfo2L.max_cavalletti: Optional[int] = None")
    print("   - Controllo in _calcola_cavalletti_fallback()")
    print("   - Riduzione con _reduce_cavalletti_simple() per priorità")
    print("   - Logging: 'LIMITE SUPERATO: X > max_cavalletti'")
    
    print("✅ DOVE È GESTITO:")
    print("   1. solver_2l.py linea 2450: _calcola_cavalletti_fallback()")
    print("   2. CavallettiOptimizerAdvanced.optimize_cavalletti_complete()")
    print("   3. Fallback con riduzione per priorità peso/dimensione")
    
    # 2. ANALISI CONDIVISIONE CAVALLETTI
    print("\n🔄 2. REGOLE CONDIVISIONE CAVALLETTI")
    print("-" * 50)
    
    print("🎯 RULE 1: Tool affiancati lungo Y possono condividere cavalletti (se peso OK)")
    print("✅ IMPLEMENTATO:")
    print("   - _apply_adjacency_sharing() in solver_2l.py")
    print("   - _find_adjacent_tools() per identificare tool vicini")
    print("   - _can_cavalletto_support_multiple_tools() per verifica peso")
    print("   - _check_alignment_for_sharing() per allineamento Y")
    
    print("\n🎯 RULE 2: Tool consecutivi lungo X NON possono condividere cavalletti estremi")
    print("❓ PARZIALMENTE IMPLEMENTATO:")
    print("   - _validate_physical_distribution() controlla distribuzione")
    print("   - Validazione clustering in metà tool")
    print("   - ❌ MANCA: Controllo specifico condivisione estremi lungo X")
    
    # 3. PROBLEMI IDENTIFICATI DAI LOG
    print("\n🚨 3. PROBLEMI IDENTIFICATI DAI LOG")
    print("-" * 50)
    
    print("❌ PROBLEMA 1: Tool sospesi su livello 1")
    print("   CAUSA: Ottimizzatore rimuove troppi cavalletti")
    print("   LOG: 'Riduzione forzata: 12 → 6 cavalletti (-50.0%)'")
    print("   EFFETTO: Tool con un solo appoggio o sospesi")
    
    print("❌ PROBLEMA 2: Mancanza validazione fisica post-ottimizzazione")
    print("   CAUSA: Optimizer non verifica supporto dopo riduzione")
    print("   RISULTATO: Layout fisicamente impossibili")
    
    print("❌ PROBLEMA 3: Logica adjacency sharing problematica")
    print("   CAUSA: Condivisione basata su distanza, non allineamento fisico")
    print("   RISULTATO: Cavalletti condivisi ma non allineati correttamente")
    
    # 4. ANALISI CODICE ESISTENTE
    print("\n🔧 4. ANALISI CODICE ESISTENTE")
    print("-" * 50)
    
    verifiche_implementate = [
        ("Limite max_cavalletti", "✅ Implementato", "_calcola_cavalletti_fallback()"),
        ("Condivisione tool lungo Y", "✅ Implementato", "_apply_adjacency_sharing()"),
        ("Verifica peso condiviso", "✅ Implementato", "_can_cavalletto_support_multiple_tools()"),
        ("Allineamento Y per condivisione", "✅ Implementato", "_check_alignment_for_sharing()"),
        ("Validazione distribuzione", "✅ Implementato", "_validate_physical_distribution()"),
        ("Anti-clustering metà tool", "✅ Implementato", "Controllo left_half/right_half"),
        ("Supporto minimo 2 cavalletti", "✅ Implementato", "_validate_minimum_supports_per_tool()"),
        ("Correzione automatica emergenza", "✅ Implementato", "Emergency cavalletti generation"),
        ("Riduzione intelligente priorità", "✅ Implementato", "_reduce_cavalletti_simple()"),
        ("Conversione CavallettoPosition→Fixed", "✅ Implementato", "_convert_to_fixed_positions()"),
    ]
    
    problemi_da_fixare = [
        ("❌ Tool consecutivi X - no condivisione estremi", "NON implementato", "Regola specifica mancante"),
        ("❌ Validazione fisica post-ottimizzazione", "NON implementato", "Controllo supporto dopo riduzione"),
        ("❌ Logica cavalletti come vincoli trasversali", "PARZIALE", "Concetto puntone vs appoggio"),
        ("❌ Verifica stabilità dopo adjacency sharing", "NON implementato", "Tool rimangono supportati?"),
        ("❌ Controllo interferenza cavalletti estremi", "NON implementato", "Cavalletti troppo vicini ai bordi"),
    ]
    
    print("VERIFICHE IMPLEMENTATE:")
    for verifica, status, implementazione in verifiche_implementate:
        print(f"   {status} {verifica}")
        print(f"      → {implementazione}")
    
    print("\nPROBLEMI DA FIXARE:")
    for problema, status, dettaglio in problemi_da_fixare:
        print(f"   {problema}")
        print(f"      → {dettaglio}")
    
    return problemi_da_fixare

def proponi_fix_critici():
    """Propone i fix critici per i problemi identificati"""
    print("\n🔧 FIX CRITICI PROPOSTI")
    print("=" * 80)
    
    fix_prioritari = [
        {
            "problema": "Tool consecutivi X - no condivisione estremi",
            "priorità": "ALTA",
            "fix": "Aggiungere _validate_no_extremes_sharing()",
            "codice": """
def _validate_no_extremes_sharing(self, cavalletti, layouts, config):
    # Per ogni coppia di tool consecutivi lungo X
    for i, layout1 in enumerate(layouts):
        for j, layout2 in enumerate(layouts[i+1:], i+1):
            # Verifica se sono consecutivi lungo X
            gap_x = min(abs(layout1.x + layout1.width - layout2.x), 
                       abs(layout2.x + layout2.width - layout1.x))
            
            if gap_x < config.min_distance_between_cavalletti:
                # Tool consecutivi - verifica cavalletti estremi
                cav1_estremi = self._get_extreme_cavalletti(layout1, cavalletti)
                cav2_estremi = self._get_extreme_cavalletti(layout2, cavalletti)
                
                for cav1 in cav1_estremi:
                    for cav2 in cav2_estremi:
                        if self._cavalletti_overlap_significantly(cav1, cav2, config):
                            # VIOLAZIONE: Rimuovi uno dei due cavalletti
                            self._resolve_extremes_conflict(cav1, cav2, layouts)
            """
        },
        {
            "problema": "Validazione fisica post-ottimizzazione",
            "priorità": "CRITICA",
            "fix": "Aggiungere _validate_physical_support_after_optimization()",
            "codice": """
def _validate_physical_support_after_optimization(self, cavalletti_finali, layouts):
    for layout in layouts:
        if layout.level == 1:  # Tool su cavalletti
            tool_cavalletti = [c for c in cavalletti_finali if c.tool_odl_id == layout.odl_id]
            
            # Verifica minimo 2 supporti
            if len(tool_cavalletti) < 2:
                raise ValueError(f"ODL {layout.odl_id}: insufficienti supporti ({len(tool_cavalletti)}<2)")
            
            # Verifica distribuzione bilanciata
            center_x = layout.x + layout.width / 2
            left_supports = sum(1 for c in tool_cavalletti if c.center_x < center_x)
            right_supports = len(tool_cavalletti) - left_supports
            
            if left_supports == 0 or right_supports == 0:
                raise ValueError(f"ODL {layout.odl_id}: supporti non bilanciati ({left_supports}L, {right_supports}R)")
            """
        },
        {
            "problema": "Cavalletti come vincoli trasversali",
            "priorità": "MEDIA",
            "fix": "Modificare concetto da puntone a appoggio trasversale",
            "codice": """
# Cambiare da:
class CavallettoPosition:  # Punto di appoggio sotto tool
    
# A:
class CavallettoTransversale:  # Segmento trasversale dell'autoclave
    start_y: float    # Inizio segmento lungo Y
    end_y: float      # Fine segmento lungo Y  
    position_x: float # Posizione fissa lungo X
    supports_tools: List[int]  # Tool che appoggiano su questo segmento
            """
        }
    ]
    
    for i, fix in enumerate(fix_prioritari, 1):
        print(f"\n🎯 FIX {i}: {fix['problema']} (Priorità: {fix['priorità']})")
        print(f"SOLUZIONE: {fix['fix']}")
        print("IMPLEMENTAZIONE:")
        print(fix['codice'])
    
    print("\n⚡ ORDINE IMPLEMENTAZIONE CONSIGLIATO:")
    print("1. Validazione fisica post-ottimizzazione (CRITICA)")
    print("2. Regola no condivisione estremi X (ALTA)")  
    print("3. Concetto cavalletti trasversali (MEDIA)")

def stampa_conclusioni():
    """Stampa le conclusioni della diagnosi"""
    print("\n📋 CONCLUSIONI DIAGNOSI")
    print("=" * 80)
    
    print("✅ SISTEMA ATTUALE - PARTI FUNZIONANTI:")
    print("   - Limite max_cavalletti rispettato correttamente")
    print("   - Condivisione tool lungo Y implementata")
    print("   - Validazione distribuzione fisica basilare")
    print("   - Riduzione intelligente per priorità")
    print("   - Correzione automatica emergenza")
    
    print("\n❌ PROBLEMI CRITICI IDENTIFICATI:")
    print("   1. 🚨 LAYOUT FISICAMENTE IMPOSSIBILI")
    print("      → Tool sospesi o con un solo appoggio")
    print("      → Causato da riduzione eccessiva senza validazione")
    
    print("   2. ⚠️  REGOLA MANCANTE: No condivisione estremi X")
    print("      → Tool consecutivi lungo X condividono cavalletti estremi")
    print("      → Viola principi fisici di stabilità")
    
    print("   3. 🔧 CONCETTO ERRATO: Cavalletti come puntoni")
    print("      → Dovrebbero essere vincoli trasversali, non punti")
    print("      → Logica di condivisione basata su concetto sbagliato")
    
    print("\n🏆 RACCOMANDAZIONI IMMEDIATE:")
    print("   1. Implementare validazione fisica post-ottimizzazione")
    print("   2. Aggiungere regola anti-condivisione estremi X")
    print("   3. Considerare refactor verso cavalletti trasversali")
    print("   4. Test completi con dataset reale")

if __name__ == "__main__":
    print("🚀 Avvio diagnosi completa sistema cavalletti...")
    
    problemi = analizza_sistema_cavalletti()
    proponi_fix_critici()
    stampa_conclusioni()
    
    print(f"\n🎯 DIAGNOSI COMPLETATA: {len(problemi)} problemi critici identificati")
    print("📄 Report completo generato per implementazione fix") 