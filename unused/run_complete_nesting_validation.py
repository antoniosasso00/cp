#!/usr/bin/env python3
"""
🚀 ORCHESTRATORE COMPLETO VALIDAZIONE NESTING
==============================================

Script principale che coordina:
1. Correzione struttura catalogo
2. Stress test completo nesting
3. Validazione algoritmo OR-Tools
4. Report finale consolidato

Questo script implementa esattamente quanto richiesto nel prompt:
- Pulizia completa database ad ogni iterazione
- Seed dati coerenti e realistici
- Test algoritmo con scenari diversificati
- Validazione vincoli fisici
- Test comportamento su 2 piani
- Rilevamento errori e dati corrotti
- Report dettagliati con diagnostica

Autore: Sistema CarbonPilot
Data: 2025-01-27
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import degli script di correzione e test
from fix_catalog_structure import CatalogStructureFixer
from stress_test_nesting_complete_v2 import StressTestNesting, TestConfig

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'complete_nesting_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteNestingValidator:
    """Orchestratore completo per la validazione del nesting"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.risultati_completi = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "versione": "2.0",
                "descrizione": "Validazione completa sistema nesting CarbonPilot"
            },
            "fase_correzione_catalogo": {},
            "fase_stress_test": {},
            "analisi_finale": {},
            "raccomandazioni_finali": []
        }
    
    def stampa_intestazione(self):
        """Stampa l'intestazione del processo"""
        print("\n" + "="*80)
        print("🚀 VALIDAZIONE COMPLETA SISTEMA NESTING CARBONPILOT")
        print("="*80)
        print("📋 FASI DEL PROCESSO:")
        print("   1. 🔧 Correzione struttura catalogo")
        print("   2. 🧪 Stress test algoritmo nesting")
        print("   3. 📊 Analisi risultati e raccomandazioni")
        print("   4. 📄 Report finale consolidato")
        print("="*80)
        print(f"⏰ Inizio processo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def fase_1_correzione_catalogo(self):
        """
        🔧 FASE 1: CORREZIONE STRUTTURA CATALOGO
        Corregge la struttura del catalogo come richiesto
        """
        logger.info("🔧 FASE 1: Correzione struttura catalogo...")
        print("\n🔧 FASE 1: CORREZIONE STRUTTURA CATALOGO")
        print("-" * 50)
        
        try:
            with CatalogStructureFixer() as fixer:
                report_correzioni = fixer.esegui_correzione_completa()
                
                self.risultati_completi["fase_correzione_catalogo"] = {
                    "completata": True,
                    "timestamp": datetime.now().isoformat(),
                    "report_file": report_correzioni,
                    "errori": []
                }
                
                logger.info("✅ Fase 1 completata con successo")
                print("✅ Correzione catalogo completata")
                
        except Exception as e:
            error_msg = f"Errore durante correzione catalogo: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self.risultati_completi["fase_correzione_catalogo"] = {
                "completata": False,
                "timestamp": datetime.now().isoformat(),
                "errori": [error_msg]
            }
            
            print(f"❌ Errore fase 1: {error_msg}")
            raise
    
    def fase_2_stress_test_nesting(self):
        """
        🧪 FASE 2: STRESS TEST NESTING
        Esegue il test di stress completo dell'algoritmo
        """
        logger.info("🧪 FASE 2: Stress test nesting...")
        print("\n🧪 FASE 2: STRESS TEST NESTING")
        print("-" * 50)
        
        try:
            # Configurazione test ottimizzata per validazione completa
            config = TestConfig(
                num_iterazioni=5,  # Più iterazioni per test approfondito
                num_odl_per_iterazione=15,  # Più ODL per stressare l'algoritmo
                percentuale_odl_validi=0.6,  # 60% ODL validi
                percentuale_odl_borderline=0.3,  # 30% ODL borderline
                percentuale_odl_errati=0.1,  # 10% ODL errati
                abilita_secondo_piano=True,
                log_dettagliato=True
            )
            
            with StressTestNesting(config) as test:
                report_stress_test = test.esegui_stress_test_completo()
                
                self.risultati_completi["fase_stress_test"] = {
                    "completata": True,
                    "timestamp": datetime.now().isoformat(),
                    "report_file": report_stress_test,
                    "configurazione": {
                        "num_iterazioni": config.num_iterazioni,
                        "num_odl_per_iterazione": config.num_odl_per_iterazione,
                        "percentuale_odl_validi": config.percentuale_odl_validi,
                        "percentuale_odl_borderline": config.percentuale_odl_borderline,
                        "percentuale_odl_errati": config.percentuale_odl_errati
                    },
                    "statistiche_globali": test.statistiche_globali,
                    "errori": []
                }
                
                logger.info("✅ Fase 2 completata con successo")
                print("✅ Stress test completato")
                
                return test.statistiche_globali
                
        except Exception as e:
            error_msg = f"Errore durante stress test: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self.risultati_completi["fase_stress_test"] = {
                "completata": False,
                "timestamp": datetime.now().isoformat(),
                "errori": [error_msg]
            }
            
            print(f"❌ Errore fase 2: {error_msg}")
            raise
    
    def fase_3_analisi_finale(self, statistiche_stress_test: Dict):
        """
        📊 FASE 3: ANALISI FINALE
        Analizza i risultati complessivi e genera raccomandazioni
        """
        logger.info("📊 FASE 3: Analisi finale...")
        print("\n📊 FASE 3: ANALISI FINALE")
        print("-" * 50)
        
        try:
            # Analisi prestazioni algoritmo
            analisi_prestazioni = self._analizza_prestazioni_algoritmo(statistiche_stress_test)
            
            # Analisi stabilità sistema
            analisi_stabilita = self._analizza_stabilita_sistema(statistiche_stress_test)
            
            # Analisi utilizzo risorse
            analisi_risorse = self._analizza_utilizzo_risorse(statistiche_stress_test)
            
            # Raccomandazioni finali
            raccomandazioni = self._genera_raccomandazioni_finali(
                analisi_prestazioni, analisi_stabilita, analisi_risorse
            )
            
            self.risultati_completi["analisi_finale"] = {
                "prestazioni_algoritmo": analisi_prestazioni,
                "stabilita_sistema": analisi_stabilita,
                "utilizzo_risorse": analisi_risorse,
                "timestamp": datetime.now().isoformat()
            }
            
            self.risultati_completi["raccomandazioni_finali"] = raccomandazioni
            
            logger.info("✅ Fase 3 completata con successo")
            print("✅ Analisi finale completata")
            
        except Exception as e:
            error_msg = f"Errore durante analisi finale: {str(e)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ Errore fase 3: {error_msg}")
            raise
    
    def _analizza_prestazioni_algoritmo(self, stats: Dict) -> Dict:
        """Analizza le prestazioni dell'algoritmo OR-Tools"""
        total_nesting = stats.get("nesting_creati", 0)
        total_falliti = stats.get("nesting_falliti", 0)
        total_odl_assegnati = stats.get("odl_assegnati", 0)
        total_odl_scartati = stats.get("odl_scartati", 0)
        
        total_tentativi = total_nesting + total_falliti
        tasso_successo = (total_nesting / total_tentativi * 100) if total_tentativi > 0 else 0
        
        total_odl = total_odl_assegnati + total_odl_scartati
        efficienza_assegnazione = (total_odl_assegnati / total_odl * 100) if total_odl > 0 else 0
        
        return {
            "tasso_successo_nesting": round(tasso_successo, 2),
            "efficienza_assegnazione_odl": round(efficienza_assegnazione, 2),
            "nesting_creati": total_nesting,
            "nesting_falliti": total_falliti,
            "odl_assegnati": total_odl_assegnati,
            "odl_scartati": total_odl_scartati,
            "valutazione": self._valuta_prestazioni(tasso_successo, efficienza_assegnazione)
        }
    
    def _analizza_stabilita_sistema(self, stats: Dict) -> Dict:
        """Analizza la stabilità del sistema"""
        errori_algoritmo = stats.get("errori_algoritmo", [])
        num_errori = len(errori_algoritmo)
        
        # Classifica stabilità
        if num_errori == 0:
            stabilita = "ECCELLENTE"
            livello = 5
        elif num_errori <= 2:
            stabilita = "BUONA"
            livello = 4
        elif num_errori <= 5:
            stabilita = "ACCETTABILE"
            livello = 3
        elif num_errori <= 10:
            stabilita = "PROBLEMATICA"
            livello = 2
        else:
            stabilita = "CRITICA"
            livello = 1
        
        return {
            "livello_stabilita": stabilita,
            "punteggio_stabilita": livello,
            "numero_errori": num_errori,
            "errori_rilevati": errori_algoritmo[:5],  # Primi 5 errori
            "sistema_stabile": num_errori <= 2
        }
    
    def _analizza_utilizzo_risorse(self, stats: Dict) -> Dict:
        """Analizza l'utilizzo delle risorse (autoclavi, secondo piano)"""
        utilizzo_secondo_piano = stats.get("utilizzo_secondo_piano", 0)
        nesting_creati = stats.get("nesting_creati", 0)
        
        percentuale_secondo_piano = (utilizzo_secondo_piano / nesting_creati * 100) if nesting_creati > 0 else 0
        
        return {
            "utilizzo_secondo_piano_volte": utilizzo_secondo_piano,
            "percentuale_utilizzo_secondo_piano": round(percentuale_secondo_piano, 2),
            "efficienza_utilizzo_spazio": self._valuta_efficienza_spazio(percentuale_secondo_piano),
            "nesting_totali": nesting_creati
        }
    
    def _valuta_prestazioni(self, tasso_successo: float, efficienza: float) -> str:
        """Valuta le prestazioni complessive"""
        media = (tasso_successo + efficienza) / 2
        
        if media >= 90:
            return "ECCELLENTI"
        elif media >= 80:
            return "OTTIME"
        elif media >= 70:
            return "BUONE"
        elif media >= 60:
            return "ACCETTABILI"
        else:
            return "INSUFFICIENTI"
    
    def _valuta_efficienza_spazio(self, percentuale: float) -> str:
        """Valuta l'efficienza di utilizzo dello spazio"""
        if percentuale >= 40:
            return "OTTIMA"
        elif percentuale >= 25:
            return "BUONA"
        elif percentuale >= 15:
            return "ACCETTABILE"
        elif percentuale > 0:
            return "BASSA"
        else:
            return "NULLA"
    
    def _genera_raccomandazioni_finali(self, prestazioni: Dict, stabilita: Dict, risorse: Dict) -> List[str]:
        """Genera raccomandazioni finali basate sull'analisi"""
        raccomandazioni = []
        
        # Raccomandazioni prestazioni
        if prestazioni["tasso_successo_nesting"] < 80:
            raccomandazioni.append("🔧 Ottimizzare parametri algoritmo OR-Tools per migliorare tasso successo")
        
        if prestazioni["efficienza_assegnazione_odl"] < 70:
            raccomandazioni.append("📋 Migliorare validazione ODL per ridurre scarti")
        
        # Raccomandazioni stabilità
        if not stabilita["sistema_stabile"]:
            raccomandazioni.append("⚠️ Sistema instabile: investigare e correggere errori algoritmo")
        
        if stabilita["numero_errori"] > 5:
            raccomandazioni.append("🚨 Troppi errori rilevati: revisione completa codice necessaria")
        
        # Raccomandazioni utilizzo risorse
        if risorse["percentuale_utilizzo_secondo_piano"] == 0:
            raccomandazioni.append("📐 Secondo piano mai utilizzato: verificare logica assegnazione")
        
        if risorse["percentuale_utilizzo_secondo_piano"] < 20:
            raccomandazioni.append("📈 Basso utilizzo secondo piano: ottimizzare algoritmo per sfruttare meglio lo spazio")
        
        # Raccomandazioni generali
        if prestazioni["valutazione"] == "ECCELLENTI" and stabilita["sistema_stabile"]:
            raccomandazioni.append("✅ Sistema pronto per produzione")
        else:
            raccomandazioni.append("🔄 Sistema necessita ulteriori ottimizzazioni prima della produzione")
        
        return raccomandazioni
    
    def fase_4_report_finale(self):
        """
        📄 FASE 4: GENERAZIONE REPORT FINALE
        Genera il report consolidato finale
        """
        logger.info("📄 FASE 4: Generazione report finale...")
        print("\n📄 FASE 4: GENERAZIONE REPORT FINALE")
        print("-" * 50)
        
        try:
            nome_file = f"complete_nesting_validation_report_{self.timestamp}.json"
            
            # Salva report JSON completo
            with open(nome_file, 'w', encoding='utf-8') as f:
                json.dump(self.risultati_completi, f, indent=2, ensure_ascii=False)
            
            # Genera anche report testuale riassuntivo
            nome_file_txt = f"complete_nesting_validation_summary_{self.timestamp}.txt"
            self._genera_report_testuale(nome_file_txt)
            
            logger.info(f"📄 Report JSON salvato in: {nome_file}")
            logger.info(f"📄 Report testuale salvato in: {nome_file_txt}")
            print(f"✅ Report salvati:")
            print(f"   • JSON completo: {nome_file}")
            print(f"   • Riassunto testuale: {nome_file_txt}")
            
            return nome_file, nome_file_txt
            
        except Exception as e:
            error_msg = f"Errore durante generazione report: {str(e)}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ Errore fase 4: {error_msg}")
            raise
    
    def _genera_report_testuale(self, nome_file: str):
        """Genera un report testuale riassuntivo"""
        with open(nome_file, 'w', encoding='utf-8') as f:
            f.write("🚀 REPORT VALIDAZIONE COMPLETA NESTING CARBONPILOT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Riassunto fasi
            f.write("📋 RIASSUNTO FASI:\n")
            f.write(f"1. Correzione catalogo: {'✅ COMPLETATA' if self.risultati_completi['fase_correzione_catalogo'].get('completata') else '❌ FALLITA'}\n")
            f.write(f"2. Stress test nesting: {'✅ COMPLETATA' if self.risultati_completi['fase_stress_test'].get('completata') else '❌ FALLITA'}\n\n")
            
            # Analisi prestazioni
            if "analisi_finale" in self.risultati_completi:
                prestazioni = self.risultati_completi["analisi_finale"]["prestazioni_algoritmo"]
                f.write("📊 PRESTAZIONI ALGORITMO:\n")
                f.write(f"• Tasso successo nesting: {prestazioni['tasso_successo_nesting']}%\n")
                f.write(f"• Efficienza assegnazione ODL: {prestazioni['efficienza_assegnazione_odl']}%\n")
                f.write(f"• Valutazione complessiva: {prestazioni['valutazione']}\n\n")
                
                stabilita = self.risultati_completi["analisi_finale"]["stabilita_sistema"]
                f.write("🔧 STABILITÀ SISTEMA:\n")
                f.write(f"• Livello stabilità: {stabilita['livello_stabilita']}\n")
                f.write(f"• Numero errori: {stabilita['numero_errori']}\n")
                f.write(f"• Sistema stabile: {'SÌ' if stabilita['sistema_stabile'] else 'NO'}\n\n")
            
            # Raccomandazioni
            f.write("💡 RACCOMANDAZIONI FINALI:\n")
            for i, raccomandazione in enumerate(self.risultati_completi["raccomandazioni_finali"], 1):
                f.write(f"{i}. {raccomandazione}\n")
    
    def stampa_riassunto_finale(self):
        """Stampa il riassunto finale del processo"""
        print("\n" + "="*80)
        print("🎯 VALIDAZIONE COMPLETA NESTING - RIASSUNTO FINALE")
        print("="*80)
        
        # Stato fasi
        fase1_ok = self.risultati_completi["fase_correzione_catalogo"].get("completata", False)
        fase2_ok = self.risultati_completi["fase_stress_test"].get("completata", False)
        
        print(f"📋 STATO FASI:")
        print(f"   1. Correzione catalogo: {'✅ COMPLETATA' if fase1_ok else '❌ FALLITA'}")
        print(f"   2. Stress test nesting: {'✅ COMPLETATA' if fase2_ok else '❌ FALLITA'}")
        
        if fase2_ok and "analisi_finale" in self.risultati_completi:
            prestazioni = self.risultati_completi["analisi_finale"]["prestazioni_algoritmo"]
            stabilita = self.risultati_completi["analisi_finale"]["stabilita_sistema"]
            
            print(f"\n📊 RISULTATI CHIAVE:")
            print(f"   • Tasso successo: {prestazioni['tasso_successo_nesting']}%")
            print(f"   • Efficienza ODL: {prestazioni['efficienza_assegnazione_odl']}%")
            print(f"   • Stabilità: {stabilita['livello_stabilita']}")
            print(f"   • Valutazione: {prestazioni['valutazione']}")
            
            print(f"\n💡 RACCOMANDAZIONI PRINCIPALI:")
            for raccomandazione in self.risultati_completi["raccomandazioni_finali"][:3]:
                print(f"   • {raccomandazione}")
        
        print("\n" + "="*80)
        print(f"⏰ Processo completato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def esegui_validazione_completa(self):
        """
        🚀 METODO PRINCIPALE
        Esegue l'intero processo di validazione
        """
        try:
            self.stampa_intestazione()
            
            # Fase 1: Correzione catalogo
            self.fase_1_correzione_catalogo()
            
            # Fase 2: Stress test nesting
            statistiche = self.fase_2_stress_test_nesting()
            
            # Fase 3: Analisi finale
            self.fase_3_analisi_finale(statistiche)
            
            # Fase 4: Report finale
            report_json, report_txt = self.fase_4_report_finale()
            
            # Riassunto finale
            self.stampa_riassunto_finale()
            
            logger.info("🎯 Validazione completa terminata con successo!")
            return report_json, report_txt
            
        except Exception as e:
            logger.error(f"❌ Errore durante validazione completa: {str(e)}")
            print(f"\n❌ PROCESSO INTERROTTO: {str(e)}")
            raise

def main():
    """Funzione principale"""
    validator = CompleteNestingValidator()
    
    try:
        report_json, report_txt = validator.esegui_validazione_completa()
        print(f"\n🎉 VALIDAZIONE COMPLETATA CON SUCCESSO!")
        print(f"📄 Report disponibili:")
        print(f"   • {report_json}")
        print(f"   • {report_txt}")
        
    except Exception as e:
        print(f"\n💥 VALIDAZIONE FALLITA: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 