#!/usr/bin/env python3
"""
🔍 DIAGNOSTICA NESTING - ANALISI E OTTIMIZZAZIONE
=================================================

Script per diagnosticare problemi nel sistema di nesting e fornire
suggerimenti di ottimizzazione per l'algoritmo OR-Tools.

Funzionalità:
- Analisi dati ODL esistenti
- Verifica integrità database
- Identificazione problemi comuni
- Suggerimenti di ottimizzazione
- Report dettagliato con grafici

Autore: Sistema CarbonPilot
Data: 2024
"""

import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from backend.models.db import get_db
from backend.models.odl import ODL
from backend.models.autoclave import Autoclave, StatoAutoclaveEnum
from backend.models.parte import Parte
from backend.models.catalogo import Catalogo
from backend.models.tool_simple import ToolSimple as Tool
from backend.models.ciclo_cura import CicloCura
from backend.models.nesting_result import NestingResult

class NestingDiagnostics:
    """Classe per la diagnostica del sistema nesting"""
    
    def __init__(self):
        self.db: Session = None
        self.report_data = {}
        
    def connetti_database(self):
        """Connette al database"""
        db_gen = get_db()
        self.db = next(db_gen)
        
    def analizza_odl_esistenti(self) -> Dict[str, Any]:
        """Analizza tutti gli ODL esistenti per identificare problemi"""
        print("🔍 Analisi ODL esistenti...")
        
        # Recupera tutti gli ODL con le loro relazioni
        odl_list = self.db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).all()
        
        analisi = {
            'totale_odl': len(odl_list),
            'per_stato': defaultdict(int),
            'problemi': {
                'senza_parte': [],
                'senza_catalogo': [],
                'superficie_zero': [],
                'senza_tool': [],
                'senza_ciclo_cura': [],
                'valvole_zero': [],
                'tool_oversize': []
            },
            'statistiche_superficie': {
                'min': float('inf'),
                'max': 0,
                'media': 0,
                'valide': 0,
                'invalide': 0
            },
            'distribuzione_cicli': defaultdict(int),
            'distribuzione_priorita': defaultdict(int)
        }
        
        superfici_valide = []
        
        for odl in odl_list:
            # Conta per stato
            analisi['per_stato'][odl.status.value] += 1
            analisi['distribuzione_priorita'][odl.priorita] += 1
            
            # Verifica problemi
            if not odl.parte:
                analisi['problemi']['senza_parte'].append(odl.id)
                continue
                
            if not odl.parte.catalogo:
                analisi['problemi']['senza_catalogo'].append(odl.id)
            else:
                # Analizza superficie
                area = odl.parte.catalogo.area_cm2
                if not area or area <= 0:
                    analisi['problemi']['superficie_zero'].append(odl.id)
                    analisi['statistiche_superficie']['invalide'] += 1
                else:
                    superfici_valide.append(area)
                    analisi['statistiche_superficie']['valide'] += 1
                    analisi['statistiche_superficie']['min'] = min(analisi['statistiche_superficie']['min'], area)
                    analisi['statistiche_superficie']['max'] = max(analisi['statistiche_superficie']['max'], area)
            
            if not odl.tool:
                analisi['problemi']['senza_tool'].append(odl.id)
            else:
                # Verifica se il tool è troppo grande per le autoclavi
                if self._tool_troppo_grande(odl.tool):
                    analisi['problemi']['tool_oversize'].append(odl.id)
            
            if not odl.parte.ciclo_cura:
                analisi['problemi']['senza_ciclo_cura'].append(odl.id)
            else:
                analisi['distribuzione_cicli'][odl.parte.ciclo_cura.nome] += 1
            
            if not odl.parte.num_valvole_richieste or odl.parte.num_valvole_richieste <= 0:
                analisi['problemi']['valvole_zero'].append(odl.id)
        
        # Calcola statistiche superficie
        if superfici_valide:
            analisi['statistiche_superficie']['media'] = sum(superfici_valide) / len(superfici_valide)
        else:
            analisi['statistiche_superficie']['min'] = 0
        
        return analisi
    
    def _tool_troppo_grande(self, tool: Tool) -> bool:
        """Verifica se un tool è troppo grande per tutte le autoclavi"""
        autoclavi = self.db.query(Autoclave).all()
        
        for autoclave in autoclavi:
            if (tool.lunghezza_piano <= autoclave.lunghezza and 
                tool.larghezza_piano <= autoclave.larghezza_piano):
                return False
        
        return True
    
    def analizza_autoclavi(self) -> Dict[str, Any]:
        """Analizza le autoclavi disponibili"""
        print("🏭 Analisi autoclavi...")
        
        autoclavi = self.db.query(Autoclave).all()
        
        analisi = {
            'totale_autoclavi': len(autoclavi),
            'per_stato': defaultdict(int),
            'capacita_totale': {
                'superficie_cm2': 0,
                'peso_kg': 0,
                'valvole': 0
            },
            'con_piano_2': 0,
            'dimensioni': {
                'lunghezza_min': float('inf'),
                'lunghezza_max': 0,
                'larghezza_min': float('inf'),
                'larghezza_max': 0
            }
        }
        
        for autoclave in autoclavi:
            analisi['per_stato'][autoclave.stato.value] += 1
            
            # Calcola capacità
            superficie = (autoclave.lunghezza * autoclave.larghezza_piano) / 100  # cm²
            analisi['capacita_totale']['superficie_cm2'] += superficie
            analisi['capacita_totale']['peso_kg'] += autoclave.peso_massimo
            analisi['capacita_totale']['valvole'] += autoclave.num_linee_vuoto
            
            if autoclave.use_secondary_plane:
                analisi['con_piano_2'] += 1
            
            # Dimensioni
            analisi['dimensioni']['lunghezza_min'] = min(analisi['dimensioni']['lunghezza_min'], autoclave.lunghezza)
            analisi['dimensioni']['lunghezza_max'] = max(analisi['dimensioni']['lunghezza_max'], autoclave.lunghezza)
            analisi['dimensioni']['larghezza_min'] = min(analisi['dimensioni']['larghezza_min'], autoclave.larghezza_piano)
            analisi['dimensioni']['larghezza_max'] = max(analisi['dimensioni']['larghezza_max'], autoclave.larghezza_piano)
        
        if not autoclavi:
            analisi['dimensioni'] = {'lunghezza_min': 0, 'lunghezza_max': 0, 'larghezza_min': 0, 'larghezza_max': 0}
        
        return analisi
    
    def analizza_nesting_storici(self) -> Dict[str, Any]:
        """Analizza i nesting storici per identificare pattern"""
        print("📊 Analisi nesting storici...")
        
        nesting_list = self.db.query(NestingResult).options(
            joinedload(NestingResult.autoclave)
        ).all()
        
        analisi = {
            'totale_nesting': len(nesting_list),
            'per_stato': defaultdict(int),
            'successi_vs_fallimenti': {'successi': 0, 'fallimenti': 0},
            'utilizzo_medio_superficie': 0,
            'odl_per_nesting': {'min': float('inf'), 'max': 0, 'media': 0},
            'autoclavi_piu_usate': defaultdict(int),
            'trend_temporale': defaultdict(int)
        }
        
        odl_counts = []
        utilizzi_superficie = []
        
        for nesting in nesting_list:
            analisi['per_stato'][nesting.stato] += 1
            
            # Conta successi/fallimenti
            if nesting.stato in ['Completato', 'In corso']:
                analisi['successi_vs_fallimenti']['successi'] += 1
            else:
                analisi['successi_vs_fallimenti']['fallimenti'] += 1
            
            # Conta ODL
            if nesting.odl_ids:
                num_odl = len(nesting.odl_ids)
                odl_counts.append(num_odl)
                analisi['odl_per_nesting']['min'] = min(analisi['odl_per_nesting']['min'], num_odl)
                analisi['odl_per_nesting']['max'] = max(analisi['odl_per_nesting']['max'], num_odl)
            
            # Autoclave più usate
            if nesting.autoclave:
                analisi['autoclavi_piu_usate'][nesting.autoclave.nome] += 1
            
            # Trend temporale (per mese)
            if nesting.created_at:
                mese = nesting.created_at.strftime('%Y-%m')
                analisi['trend_temporale'][mese] += 1
            
            # Utilizzo superficie (se disponibile nei dati JSON)
            if nesting.layout_data:
                try:
                    layout = json.loads(nesting.layout_data) if isinstance(nesting.layout_data, str) else nesting.layout_data
                    if 'utilizzo_superficie' in layout:
                        utilizzi_superficie.append(layout['utilizzo_superficie'])
                except:
                    pass
        
        # Calcola medie
        if odl_counts:
            analisi['odl_per_nesting']['media'] = sum(odl_counts) / len(odl_counts)
        else:
            analisi['odl_per_nesting']['min'] = 0
        
        if utilizzi_superficie:
            analisi['utilizzo_medio_superficie'] = sum(utilizzi_superficie) / len(utilizzi_superficie)
        
        return analisi
    
    def identifica_problemi_critici(self, analisi_odl: Dict, analisi_autoclavi: Dict) -> List[Dict[str, Any]]:
        """Identifica i problemi più critici che impediscono il nesting"""
        problemi_critici = []
        
        # Problema 1: ODL senza superficie valida
        odl_superficie_problemi = len(analisi_odl['problemi']['superficie_zero'])
        if odl_superficie_problemi > 0:
            problemi_critici.append({
                'tipo': 'CRITICO',
                'categoria': 'Dati ODL',
                'problema': f'{odl_superficie_problemi} ODL hanno superficie zero o non definita',
                'impatto': 'Questi ODL vengono automaticamente esclusi dal nesting',
                'soluzione': 'Aggiornare il catalogo parti con le superfici corrette',
                'odl_interessati': analisi_odl['problemi']['superficie_zero'][:10]  # Primi 10
            })
        
        # Problema 2: ODL senza tool
        odl_senza_tool = len(analisi_odl['problemi']['senza_tool'])
        if odl_senza_tool > 0:
            problemi_critici.append({
                'tipo': 'CRITICO',
                'categoria': 'Assegnazione Tool',
                'problema': f'{odl_senza_tool} ODL non hanno tool assegnato',
                'impatto': 'Impossibile calcolare posizionamento nel nesting',
                'soluzione': 'Assegnare tool appropriati agli ODL',
                'odl_interessati': analisi_odl['problemi']['senza_tool'][:10]
            })
        
        # Problema 3: Tool troppo grandi
        tool_oversize = len(analisi_odl['problemi']['tool_oversize'])
        if tool_oversize > 0:
            problemi_critici.append({
                'tipo': 'ALTO',
                'categoria': 'Compatibilità Dimensioni',
                'problema': f'{tool_oversize} ODL hanno tool troppo grandi per le autoclavi',
                'impatto': 'Questi ODL non possono essere processati',
                'soluzione': 'Verificare dimensioni tool o aggiungere autoclavi più grandi',
                'odl_interessati': analisi_odl['problemi']['tool_oversize'][:10]
            })
        
        # Problema 4: Nessuna autoclave disponibile
        autoclavi_disponibili = analisi_autoclavi['per_stato'].get('DISPONIBILE', 0)
        if autoclavi_disponibili == 0:
            problemi_critici.append({
                'tipo': 'CRITICO',
                'categoria': 'Disponibilità Autoclavi',
                'problema': 'Nessuna autoclave disponibile',
                'impatto': 'Impossibile creare qualsiasi nesting',
                'soluzione': 'Liberare almeno una autoclave o aggiungerne di nuove',
                'odl_interessati': []
            })
        
        # Problema 5: ODL senza ciclo di cura
        odl_senza_ciclo = len(analisi_odl['problemi']['senza_ciclo_cura'])
        if odl_senza_ciclo > 0:
            problemi_critici.append({
                'tipo': 'ALTO',
                'categoria': 'Configurazione Processo',
                'problema': f'{odl_senza_ciclo} ODL non hanno ciclo di cura definito',
                'impatto': 'Impossibile raggruppare ODL compatibili',
                'soluzione': 'Assegnare cicli di cura appropriati alle parti',
                'odl_interessati': analisi_odl['problemi']['senza_ciclo_cura'][:10]
            })
        
        return problemi_critici
    
    def genera_suggerimenti_ottimizzazione(self, analisi_odl: Dict, analisi_autoclavi: Dict, analisi_nesting: Dict) -> List[Dict[str, Any]]:
        """Genera suggerimenti per ottimizzare il sistema"""
        suggerimenti = []
        
        # Suggerimento 1: Utilizzo superficie
        if analisi_nesting['utilizzo_medio_superficie'] > 0 and analisi_nesting['utilizzo_medio_superficie'] < 70:
            suggerimenti.append({
                'categoria': 'Efficienza',
                'suggerimento': f'Utilizzo superficie medio basso ({analisi_nesting["utilizzo_medio_superficie"]:.1f}%)',
                'azione': 'Considerare algoritmi di packing più aggressivi o raggruppamento ODL più intelligente',
                'beneficio': 'Aumento capacità produttiva del 15-25%'
            })
        
        # Suggerimento 2: Bilanciamento autoclavi
        if analisi_autoclavi['con_piano_2'] < analisi_autoclavi['totale_autoclavi'] / 2:
            suggerimenti.append({
                'categoria': 'Capacità',
                'suggerimento': 'Poche autoclavi hanno il secondo piano attivo',
                'azione': 'Attivare il secondo piano su più autoclavi per aumentare capacità',
                'beneficio': 'Aumento capacità fino al 50% per autoclave'
            })
        
        # Suggerimento 3: Distribuzione priorità
        priorita_alta = analisi_odl['distribuzione_priorita'].get(5, 0) + analisi_odl['distribuzione_priorita'].get(4, 0)
        if priorita_alta > analisi_odl['totale_odl'] * 0.7:
            suggerimenti.append({
                'categoria': 'Pianificazione',
                'suggerimento': 'Troppi ODL con priorità alta (>70%)',
                'azione': 'Rivedere sistema di priorità per migliorare pianificazione',
                'beneficio': 'Migliore gestione code e tempi di consegna'
            })
        
        # Suggerimento 4: Varietà cicli di cura
        num_cicli_diversi = len(analisi_odl['distribuzione_cicli'])
        if num_cicli_diversi > 5:
            suggerimenti.append({
                'categoria': 'Standardizzazione',
                'suggerimento': f'Molti cicli di cura diversi ({num_cicli_diversi})',
                'azione': 'Standardizzare cicli di cura per migliorare raggruppamento ODL',
                'beneficio': 'Nesting più efficienti e meno cambi setup'
            })
        
        return suggerimenti
    
    def genera_report_completo(self) -> Dict[str, Any]:
        """Genera un report completo di diagnostica"""
        print("📋 Generazione report completo...")
        
        # Esegui tutte le analisi
        analisi_odl = self.analizza_odl_esistenti()
        analisi_autoclavi = self.analizza_autoclavi()
        analisi_nesting = self.analizza_nesting_storici()
        
        # Identifica problemi e suggerimenti
        problemi_critici = self.identifica_problemi_critici(analisi_odl, analisi_autoclavi)
        suggerimenti = self.genera_suggerimenti_ottimizzazione(analisi_odl, analisi_autoclavi, analisi_nesting)
        
        # Calcola score di salute del sistema
        score_salute = self._calcola_score_salute(analisi_odl, analisi_autoclavi, problemi_critici)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'score_salute': score_salute,
            'analisi_odl': analisi_odl,
            'analisi_autoclavi': analisi_autoclavi,
            'analisi_nesting': analisi_nesting,
            'problemi_critici': problemi_critici,
            'suggerimenti_ottimizzazione': suggerimenti,
            'raccomandazioni_immediate': self._genera_raccomandazioni_immediate(problemi_critici)
        }
        
        return report
    
    def _calcola_score_salute(self, analisi_odl: Dict, analisi_autoclavi: Dict, problemi_critici: List) -> Dict[str, Any]:
        """Calcola un score di salute del sistema (0-100)"""
        score = 100
        dettagli = []
        
        # Penalità per ODL con problemi
        odl_validi = analisi_odl['statistiche_superficie']['valide']
        odl_totali = analisi_odl['totale_odl']
        
        if odl_totali > 0:
            percentuale_validi = (odl_validi / odl_totali) * 100
            if percentuale_validi < 90:
                penalita = (90 - percentuale_validi) * 0.5
                score -= penalita
                dettagli.append(f"ODL validi: {percentuale_validi:.1f}% (-{penalita:.1f} punti)")
        
        # Penalità per autoclavi non disponibili
        autoclavi_disponibili = analisi_autoclavi['per_stato'].get('DISPONIBILE', 0)
        autoclavi_totali = analisi_autoclavi['totale_autoclavi']
        
        if autoclavi_totali > 0:
            percentuale_disponibili = (autoclavi_disponibili / autoclavi_totali) * 100
            if percentuale_disponibili < 50:
                penalita = (50 - percentuale_disponibili) * 0.3
                score -= penalita
                dettagli.append(f"Autoclavi disponibili: {percentuale_disponibili:.1f}% (-{penalita:.1f} punti)")
        
        # Penalità per problemi critici
        problemi_critici_count = sum(1 for p in problemi_critici if p['tipo'] == 'CRITICO')
        if problemi_critici_count > 0:
            penalita = problemi_critici_count * 15
            score -= penalita
            dettagli.append(f"Problemi critici: {problemi_critici_count} (-{penalita} punti)")
        
        score = max(0, score)  # Non può essere negativo
        
        # Determina livello di salute
        if score >= 90:
            livello = "ECCELLENTE"
        elif score >= 75:
            livello = "BUONO"
        elif score >= 50:
            livello = "ACCETTABILE"
        elif score >= 25:
            livello = "PROBLEMATICO"
        else:
            livello = "CRITICO"
        
        return {
            'score': round(score, 1),
            'livello': livello,
            'dettagli': dettagli
        }
    
    def _genera_raccomandazioni_immediate(self, problemi_critici: List) -> List[str]:
        """Genera raccomandazioni immediate basate sui problemi critici"""
        raccomandazioni = []
        
        for problema in problemi_critici:
            if problema['tipo'] == 'CRITICO':
                raccomandazioni.append(f"🚨 URGENTE: {problema['soluzione']}")
            elif problema['tipo'] == 'ALTO':
                raccomandazioni.append(f"⚠️ IMPORTANTE: {problema['soluzione']}")
        
        if not raccomandazioni:
            raccomandazioni.append("✅ Nessuna azione critica richiesta")
        
        return raccomandazioni
    
    def stampa_report_console(self, report: Dict):
        """Stampa il report in console in formato leggibile"""
        print("\n" + "="*80)
        print("🔍 REPORT DIAGNOSTICA SISTEMA NESTING")
        print("="*80)
        
        # Score di salute
        score_info = report['score_salute']
        print(f"\n🏥 SALUTE SISTEMA: {score_info['score']}/100 - {score_info['livello']}")
        for dettaglio in score_info['dettagli']:
            print(f"   {dettaglio}")
        
        # Statistiche generali
        print(f"\n📊 STATISTICHE GENERALI:")
        print(f"   ODL totali: {report['analisi_odl']['totale_odl']}")
        print(f"   ODL validi per nesting: {report['analisi_odl']['statistiche_superficie']['valide']}")
        print(f"   Autoclavi totali: {report['analisi_autoclavi']['totale_autoclavi']}")
        print(f"   Autoclavi disponibili: {report['analisi_autoclavi']['per_stato'].get('DISPONIBILE', 0)}")
        print(f"   Nesting storici: {report['analisi_nesting']['totale_nesting']}")
        
        # Problemi critici
        print(f"\n🚨 PROBLEMI CRITICI ({len(report['problemi_critici'])}):")
        for problema in report['problemi_critici']:
            print(f"   {problema['tipo']}: {problema['problema']}")
            print(f"      Soluzione: {problema['soluzione']}")
        
        # Raccomandazioni immediate
        print(f"\n💡 RACCOMANDAZIONI IMMEDIATE:")
        for raccomandazione in report['raccomandazioni_immediate']:
            print(f"   {raccomandazione}")
        
        # Suggerimenti ottimizzazione
        print(f"\n🎯 SUGGERIMENTI OTTIMIZZAZIONE:")
        for suggerimento in report['suggerimenti_ottimizzazione']:
            print(f"   {suggerimento['categoria']}: {suggerimento['suggerimento']}")
            print(f"      Azione: {suggerimento['azione']}")
            print(f"      Beneficio: {suggerimento['beneficio']}")
        
        print("\n" + "="*80)
    
    def salva_report_json(self, report: Dict, filename: str = None):
        """Salva il report in formato JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nesting_diagnostics_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Report salvato in: {filename}")

def main():
    """Funzione principale"""
    print("🔍 DIAGNOSTICA SISTEMA NESTING")
    print("Analisi completa e suggerimenti di ottimizzazione")
    print("-" * 50)
    
    # Crea diagnostica
    diagnostics = NestingDiagnostics()
    diagnostics.connetti_database()
    
    try:
        # Genera report completo
        report = diagnostics.genera_report_completo()
        
        # Stampa in console
        diagnostics.stampa_report_console(report)
        
        # Salva in JSON
        diagnostics.salva_report_json(report)
        
        print("\n✅ DIAGNOSTICA COMPLETATA!")
        
    finally:
        diagnostics.db.close()

if __name__ == "__main__":
    main() 