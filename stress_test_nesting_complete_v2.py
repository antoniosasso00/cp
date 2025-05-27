#!/usr/bin/env python3
"""
🧪 STRESS TEST COMPLETO NESTING + VALIDAZIONE OR-TOOLS
=======================================================

Sistema completo per testare e validare l'algoritmo di nesting:
- Pulizia completa database
- Generazione seed dati realistici
- Test algoritmo OR-Tools con scenari multipli
- Validazione vincoli fisici (peso, superficie, valvole)
- Test comportamento su 2 piani
- Rilevamento errori e dati corrotti
- Report dettagliati con diagnostica

Autore: Sistema CarbonPilot
Data: 2025-01-27
"""

import os
import sys
import json
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session, joinedload
from models.db import SessionLocal, engine
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL, StatoODLEnum
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.ciclo_cura import CicloCura
from models.nesting_result import NestingResult
from models.report import Report
from nesting_optimizer.auto_nesting import compute_nesting, validate_odl_for_nesting

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'stress_test_nesting_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Configurazione per il test di stress"""
    num_iterazioni: int = 3
    num_autoclavi: int = 2
    num_odl_per_iterazione: int = 10
    percentuale_odl_validi: float = 0.7
    percentuale_odl_borderline: float = 0.2
    percentuale_odl_errati: float = 0.1
    abilita_secondo_piano: bool = True
    log_dettagliato: bool = True

class StressTestNesting:
    """Classe principale per il test di stress del nesting"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.db = SessionLocal()
        self.risultati_test: List[Dict] = []
        self.statistiche_globali = {
            "nesting_creati": 0,
            "nesting_falliti": 0,
            "odl_assegnati": 0,
            "odl_scartati": 0,
            "errori_algoritmo": [],
            "utilizzo_secondo_piano": 0
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def pulisci_database_completo(self):
        """
        🧹 PULIZIA COMPLETA DATABASE
        Rimuove tutti i dati dalle tabelle principali per iniziare con uno stato pulito
        """
        logger.info("🧹 Inizio pulizia completa database...")
        
        try:
            # Ordine di eliminazione per rispettare le foreign key
            tabelle_da_pulire = [
                "nesting_results",
                "reports", 
                "odl",
                "parti",
                "tools",
                "cataloghi",
                "autoclavi",
                "cicli_cura"
            ]
            
            for tabella in tabelle_da_pulire:
                result = self.db.execute(f"DELETE FROM {tabella}")
                logger.info(f"   ✅ Eliminati {result.rowcount} record da {tabella}")
            
            self.db.commit()
            logger.info("🧹 Pulizia database completata con successo!")
            
        except Exception as e:
            logger.error(f"❌ Errore durante pulizia database: {str(e)}")
            self.db.rollback()
            raise
    
    def crea_seed_dati_realistici(self, iterazione: int):
        """
        🌱 CREAZIONE SEED DATI REALISTICI
        Genera dati di test con scenari diversificati per ogni iterazione
        """
        logger.info(f"🌱 Creazione seed dati per iterazione #{iterazione}...")
        
        # 1. Crea cicli di cura
        cicli_cura = self._crea_cicli_cura()
        
        # 2. Crea autoclavi
        autoclavi = self._crea_autoclavi()
        
        # 3. Crea catalogo e tools
        cataloghi, tools = self._crea_catalogo_e_tools(iterazione)
        
        # 4. Crea parti
        parti = self._crea_parti(cataloghi, cicli_cura, tools)
        
        # 5. Crea ODL con scenari diversificati
        odl_list = self._crea_odl_diversificati(parti, tools, iterazione)
        
        self.db.commit()
        
        logger.info(f"🌱 Seed dati creati: {len(autoclavi)} autoclavi, {len(odl_list)} ODL")
        return autoclavi, odl_list
    
    def _crea_cicli_cura(self) -> List[CicloCura]:
        """Crea cicli di cura standard"""
        cicli = [
            CicloCura(
                nome="Standard_120C",
                temperatura=120.0,
                pressione=2.0,
                durata_minuti=180,
                descrizione="Ciclo standard 120°C per materiali compositi"
            ),
            CicloCura(
                nome="High_Temp_180C", 
                temperatura=180.0,
                pressione=3.0,
                durata_minuti=240,
                descrizione="Ciclo alta temperatura per materiali speciali"
            ),
            CicloCura(
                nome="Low_Temp_80C",
                temperatura=80.0,
                pressione=1.5,
                durata_minuti=120,
                descrizione="Ciclo bassa temperatura per materiali delicati"
            )
        ]
        
        for ciclo in cicli:
            self.db.add(ciclo)
        self.db.flush()
        
        return cicli
    
    def _crea_autoclavi(self) -> List[Autoclave]:
        """Crea autoclavi con configurazioni diverse"""
        autoclavi = [
            Autoclave(
                nome="AUTO-001-STANDARD",
                larghezza_piano_mm=1200.0,
                lunghezza_piano_mm=2000.0,
                altezza_utile_mm=800.0,
                peso_max_kg=500.0,
                num_valvole_disponibili=12,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                secondo_piano_attivo=False,
                larghezza_secondo_piano_mm=None,
                lunghezza_secondo_piano_mm=None,
                peso_max_secondo_piano_kg=None
            ),
            Autoclave(
                nome="AUTO-002-DUAL-LEVEL",
                larghezza_piano_mm=1500.0,
                lunghezza_piano_mm=2500.0,
                altezza_utile_mm=1200.0,
                peso_max_kg=800.0,
                num_valvole_disponibili=16,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                secondo_piano_attivo=True,
                larghezza_secondo_piano_mm=1400.0,
                lunghezza_secondo_piano_mm=2400.0,
                peso_max_secondo_piano_kg=300.0
            )
        ]
        
        for autoclave in autoclavi:
            self.db.add(autoclave)
        self.db.flush()
        
        return autoclavi
    
    def _crea_catalogo_e_tools(self, iterazione: int) -> Tuple[List[Catalogo], List[Tool]]:
        """Crea catalogo e tools con dimensioni realistiche"""
        cataloghi = []
        tools = []
        
        # Definizioni base per i part numbers
        part_numbers_base = [
            ("PN-WING-001", "Ala principale aereo", "Aeronautica", "Strutturale"),
            ("PN-FUSE-002", "Fusoliera sezione centrale", "Aeronautica", "Strutturale"), 
            ("PN-TAIL-003", "Stabilizzatore verticale", "Aeronautica", "Controllo"),
            ("PN-PANEL-004", "Pannello interno cabina", "Aeronautica", "Interni"),
            ("PN-BLADE-005", "Pala elica composita", "Aeronautica", "Propulsione"),
            ("PN-DOOR-006", "Portello accesso", "Aeronautica", "Accesso"),
            ("PN-FLOOR-007", "Pavimento cabina", "Aeronautica", "Interni"),
            ("PN-COWL-008", "Carenatura motore", "Aeronautica", "Propulsione")
        ]
        
        for i, (base_pn, desc, cat, subcat) in enumerate(part_numbers_base):
            # Varia il part number per ogni iterazione
            part_number = f"{base_pn}-IT{iterazione:02d}"
            
            # Crea catalogo
            catalogo = Catalogo(
                part_number=part_number,
                descrizione=f"{desc} - Iterazione {iterazione}",
                categoria=cat,
                sotto_categoria=subcat,
                attivo=True
            )
            cataloghi.append(catalogo)
            self.db.add(catalogo)
            
            # Crea tool corrispondente con dimensioni variabili
            base_length = 300 + (i * 50) + random.randint(-50, 100)  # 250-450mm
            base_width = 200 + (i * 30) + random.randint(-30, 80)    # 170-380mm
            peso_base = 5.0 + (i * 2.0) + random.uniform(-2.0, 5.0) # 3-20kg
            
            tool = Tool(
                part_number_tool=f"TOOL-{part_number}",
                descrizione=f"Stampo per {desc}",
                lunghezza_piano=float(base_length),
                larghezza_piano=float(base_width),
                peso=max(1.0, peso_base),  # Peso minimo 1kg
                materiale="Alluminio" if i % 2 == 0 else "Acciaio",
                disponibile=True
            )
            tools.append(tool)
            self.db.add(tool)
        
        self.db.flush()
        return cataloghi, tools
    
    def _crea_parti(self, cataloghi: List[Catalogo], cicli_cura: List[CicloCura], tools: List[Tool]) -> List[Parte]:
        """Crea parti collegando cataloghi, cicli di cura e tools"""
        parti = []
        
        for i, catalogo in enumerate(cataloghi):
            # Assegna ciclo di cura in modo variabile
            ciclo_cura = cicli_cura[i % len(cicli_cura)]
            
            # Numero valvole basato sulla dimensione del tool
            tool = tools[i]
            area_tool_cm2 = (tool.lunghezza_piano * tool.larghezza_piano) / 100
            num_valvole = max(1, int(area_tool_cm2 / 100))  # 1 valvola ogni 100 cm²
            
            parte = Parte(
                part_number=catalogo.part_number,
                descrizione_breve=catalogo.descrizione,
                descrizione_completa=f"Descrizione completa per {catalogo.part_number}",
                num_valvole_richieste=num_valvole,
                ciclo_cura_id=ciclo_cura.id,
                attiva=True
            )
            
            # Collega il tool alla parte
            parte.tools.append(tool)
            
            parti.append(parte)
            self.db.add(parte)
        
        self.db.flush()
        return parti
    
    def _crea_odl_diversificati(self, parti: List[Parte], tools: List[Tool], iterazione: int) -> List[ODL]:
        """
        Crea ODL con scenari diversificati:
        - 70% ODL validi e ottimali
        - 20% ODL borderline (superficie limite, peso limite)
        - 10% ODL errati (senza tool, oversize, ciclo incompatibile)
        """
        odl_list = []
        num_odl = self.config.num_odl_per_iterazione
        
        # Calcola quanti ODL per categoria
        num_validi = int(num_odl * self.config.percentuale_odl_validi)
        num_borderline = int(num_odl * self.config.percentuale_odl_borderline)
        num_errati = num_odl - num_validi - num_borderline
        
        logger.info(f"   📊 Creazione ODL: {num_validi} validi, {num_borderline} borderline, {num_errati} errati")
        
        # 1. ODL VALIDI
        for i in range(num_validi):
            parte = random.choice(parti)
            tool = random.choice([t for t in tools if t in parte.tools])
            
            odl = ODL(
                numero_odl=f"ODL-{iterazione:02d}-V{i+1:03d}",
                parte_id=parte.id,
                tool_id=tool.id,
                quantita=random.randint(1, 5),
                priorita=random.randint(1, 5),
                data_richiesta=datetime.now() - timedelta(days=random.randint(1, 30)),
                data_consegna_richiesta=datetime.now() + timedelta(days=random.randint(7, 60)),
                stato=StatoODLEnum.CONFERMATO,
                note=f"ODL valido per test iterazione {iterazione}"
            )
            odl_list.append(odl)
            self.db.add(odl)
        
        # 2. ODL BORDERLINE
        for i in range(num_borderline):
            parte = random.choice(parti)
            tool = random.choice([t for t in tools if t in parte.tools])
            
            # Modifica il tool per renderlo borderline
            if random.choice([True, False]):
                # Tool con dimensioni al limite
                tool.lunghezza_piano = 800.0  # Vicino al limite autoclave
                tool.larghezza_piano = 600.0
                tool.peso = 45.0  # Peso elevato
            
            odl = ODL(
                numero_odl=f"ODL-{iterazione:02d}-B{i+1:03d}",
                parte_id=parte.id,
                tool_id=tool.id,
                quantita=random.randint(3, 8),  # Quantità più alta
                priorita=random.randint(3, 5),
                data_richiesta=datetime.now() - timedelta(days=random.randint(1, 15)),
                data_consegna_richiesta=datetime.now() + timedelta(days=random.randint(3, 30)),
                stato=StatoODLEnum.CONFERMATO,
                note=f"ODL borderline per test iterazione {iterazione}"
            )
            odl_list.append(odl)
            self.db.add(odl)
        
        # 3. ODL ERRATI
        for i in range(num_errati):
            parte = random.choice(parti)
            
            # Crea scenari di errore diversi
            errore_tipo = random.choice(["no_tool", "oversize", "ciclo_incompatibile"])
            
            if errore_tipo == "no_tool":
                # ODL senza tool associato
                odl = ODL(
                    numero_odl=f"ODL-{iterazione:02d}-E{i+1:03d}",
                    parte_id=parte.id,
                    tool_id=None,  # ERRORE: Nessun tool
                    quantita=random.randint(1, 3),
                    priorita=random.randint(1, 3),
                    data_richiesta=datetime.now() - timedelta(days=random.randint(1, 10)),
                    data_consegna_richiesta=datetime.now() + timedelta(days=random.randint(5, 20)),
                    stato=StatoODLEnum.CONFERMATO,
                    note=f"ODL ERRATO (no tool) per test iterazione {iterazione}"
                )
            
            elif errore_tipo == "oversize":
                # Tool troppo grande per qualsiasi autoclave
                tool_oversize = Tool(
                    part_number_tool=f"TOOL-OVERSIZE-{iterazione}-{i}",
                    descrizione="Tool troppo grande per test",
                    lunghezza_piano=3000.0,  # 3 metri - troppo grande!
                    larghezza_piano=2000.0,  # 2 metri - troppo grande!
                    peso=100.0,  # Troppo pesante
                    materiale="Acciaio",
                    disponibile=True
                )
                self.db.add(tool_oversize)
                self.db.flush()
                
                odl = ODL(
                    numero_odl=f"ODL-{iterazione:02d}-E{i+1:03d}",
                    parte_id=parte.id,
                    tool_id=tool_oversize.id,
                    quantita=1,
                    priorita=1,
                    data_richiesta=datetime.now() - timedelta(days=random.randint(1, 10)),
                    data_consegna_richiesta=datetime.now() + timedelta(days=random.randint(5, 20)),
                    stato=StatoODLEnum.CONFERMATO,
                    note=f"ODL ERRATO (oversize) per test iterazione {iterazione}"
                )
            
            else:  # ciclo_incompatibile
                # ODL con parte che ha ciclo di cura incompatibile
                tool = random.choice([t for t in tools if t in parte.tools])
                odl = ODL(
                    numero_odl=f"ODL-{iterazione:02d}-E{i+1:03d}",
                    parte_id=parte.id,
                    tool_id=tool.id,
                    quantita=random.randint(1, 3),
                    priorita=random.randint(1, 3),
                    data_richiesta=datetime.now() - timedelta(days=random.randint(1, 10)),
                    data_consegna_richiesta=datetime.now() + timedelta(days=random.randint(5, 20)),
                    stato=StatoODLEnum.BOZZA,  # ERRORE: Stato non confermato
                    note=f"ODL ERRATO (stato bozza) per test iterazione {iterazione}"
                )
            
            odl_list.append(odl)
            self.db.add(odl)
        
        self.db.flush()
        return odl_list
    
    def esegui_test_nesting(self, iterazione: int, autoclavi: List[Autoclave], odl_list: List[ODL]) -> Dict:
        """
        🧪 ESECUZIONE TEST NESTING
        Testa l'algoritmo di nesting con gli ODL generati
        """
        logger.info(f"🧪 Inizio test nesting iterazione #{iterazione}...")
        
        risultato_iterazione = {
            "iterazione": iterazione,
            "timestamp": datetime.now().isoformat(),
            "odl_totali": len(odl_list),
            "autoclavi_disponibili": len(autoclavi),
            "nesting_creati": [],
            "nesting_falliti": [],
            "odl_scartati": [],
            "odl_assegnati": [],
            "utilizzo_secondo_piano": [],
            "errori_algoritmo": [],
            "statistiche": {}
        }
        
        try:
            # 1. Validazione preliminare ODL
            logger.info("   🔍 Validazione preliminare ODL...")
            odl_validi = []
            odl_non_validi = []
            
            for odl in odl_list:
                is_valid, error_msg, data = validate_odl_for_nesting(self.db, odl)
                if is_valid:
                    odl_validi.append(odl)
                else:
                    odl_non_validi.append({
                        "odl_id": odl.id,
                        "numero_odl": odl.numero_odl,
                        "motivo": error_msg
                    })
                    logger.warning(f"   ⚠️ ODL {odl.numero_odl} non valido: {error_msg}")
            
            risultato_iterazione["odl_scartati"] = odl_non_validi
            logger.info(f"   ✅ ODL validi: {len(odl_validi)}/{len(odl_list)}")
            
            # 2. Esecuzione algoritmo nesting
            if odl_validi:
                logger.info("   🔄 Esecuzione algoritmo OR-Tools...")
                
                nesting_result = compute_nesting(
                    db=self.db,
                    odl_list=odl_validi,
                    autoclavi=autoclavi
                )
                
                # 3. Analisi risultati nesting
                for autoclave_id, odl_ids in nesting_result.assegnamenti.items():
                    autoclave = self.db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
                    
                    nesting_info = {
                        "autoclave_id": autoclave_id,
                        "autoclave_nome": autoclave.nome,
                        "odl_assegnati": odl_ids,
                        "num_odl": len(odl_ids),
                        "utilizzo_secondo_piano": autoclave.secondo_piano_attivo and len(odl_ids) > 6,
                        "posizioni_tool": nesting_result.posizioni_tool.get(autoclave_id, []),
                        "statistiche": nesting_result.statistiche_autoclavi.get(autoclave_id, {}),
                        "ciclo_cura": nesting_result.cicli_cura_autoclavi.get(autoclave_id, {})
                    }
                    
                    risultato_iterazione["nesting_creati"].append(nesting_info)
                    risultato_iterazione["odl_assegnati"].extend(odl_ids)
                    
                    if nesting_info["utilizzo_secondo_piano"]:
                        risultato_iterazione["utilizzo_secondo_piano"].append(autoclave_id)
                        self.statistiche_globali["utilizzo_secondo_piano"] += 1
                    
                    logger.info(f"   ✅ Nesting creato su {autoclave.nome}: {len(odl_ids)} ODL")
                
                # 4. ODL non assegnabili
                for odl_info in nesting_result.odl_non_pianificabili:
                    risultato_iterazione["odl_scartati"].append(odl_info)
                    logger.warning(f"   ⚠️ ODL {odl_info['odl_id']} non pianificabile: {odl_info['motivo']}")
                
                # 5. Aggiorna statistiche globali
                self.statistiche_globali["nesting_creati"] += len(nesting_result.assegnamenti)
                self.statistiche_globali["odl_assegnati"] += len(risultato_iterazione["odl_assegnati"])
                self.statistiche_globali["odl_scartati"] += len(risultato_iterazione["odl_scartati"])
                
            else:
                logger.warning("   ⚠️ Nessun ODL valido per il nesting")
                risultato_iterazione["nesting_falliti"].append({
                    "motivo": "Nessun ODL valido disponibile",
                    "dettagli": "Tutti gli ODL sono stati scartati durante la validazione"
                })
                self.statistiche_globali["nesting_falliti"] += 1
        
        except Exception as e:
            logger.error(f"   ❌ Errore durante test nesting: {str(e)}")
            risultato_iterazione["errori_algoritmo"].append({
                "tipo": "Errore algoritmo",
                "messaggio": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.statistiche_globali["errori_algoritmo"].append(str(e))
            self.statistiche_globali["nesting_falliti"] += 1
        
        return risultato_iterazione
    
    def genera_report_finale(self):
        """
        📊 GENERAZIONE REPORT FINALE
        Crea un report completo con tutti i risultati del test
        """
        logger.info("📊 Generazione report finale...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"stress_test_nesting_report_{timestamp}.json"
        
        report_finale = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "configurazione": {
                    "num_iterazioni": self.config.num_iterazioni,
                    "num_autoclavi": self.config.num_autoclavi,
                    "num_odl_per_iterazione": self.config.num_odl_per_iterazione,
                    "percentuale_odl_validi": self.config.percentuale_odl_validi,
                    "percentuale_odl_borderline": self.config.percentuale_odl_borderline,
                    "percentuale_odl_errati": self.config.percentuale_odl_errati
                }
            },
            "statistiche_globali": self.statistiche_globali,
            "risultati_per_iterazione": self.risultati_test,
            "analisi_prestazioni": self._analizza_prestazioni(),
            "raccomandazioni": self._genera_raccomandazioni()
        }
        
        # Salva report su file
        with open(nome_file, 'w', encoding='utf-8') as f:
            json.dump(report_finale, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Report salvato in: {nome_file}")
        
        # Stampa riassunto
        self._stampa_riassunto_finale()
        
        return nome_file
    
    def _analizza_prestazioni(self) -> Dict:
        """Analizza le prestazioni dell'algoritmo"""
        if not self.risultati_test:
            return {}
        
        # Calcola metriche di prestazione
        total_odl = sum(r["odl_totali"] for r in self.risultati_test)
        total_assegnati = len(set().union(*[r["odl_assegnati"] for r in self.risultati_test]))
        total_scartati = sum(len(r["odl_scartati"]) for r in self.risultati_test)
        
        tasso_successo = (total_assegnati / total_odl * 100) if total_odl > 0 else 0
        tasso_scarto = (total_scartati / total_odl * 100) if total_odl > 0 else 0
        
        return {
            "tasso_successo_percentuale": round(tasso_successo, 2),
            "tasso_scarto_percentuale": round(tasso_scarto, 2),
            "odl_totali_processati": total_odl,
            "odl_assegnati_totali": total_assegnati,
            "odl_scartati_totali": total_scartati,
            "utilizzo_medio_autoclavi": self._calcola_utilizzo_medio_autoclavi(),
            "efficienza_secondo_piano": self._calcola_efficienza_secondo_piano()
        }
    
    def _calcola_utilizzo_medio_autoclavi(self) -> float:
        """Calcola l'utilizzo medio delle autoclavi"""
        utilizzi = []
        for risultato in self.risultati_test:
            for nesting in risultato["nesting_creati"]:
                if "statistiche" in nesting and "utilizzo_superficie_percentuale" in nesting["statistiche"]:
                    utilizzi.append(nesting["statistiche"]["utilizzo_superficie_percentuale"])
        
        return round(sum(utilizzi) / len(utilizzi), 2) if utilizzi else 0.0
    
    def _calcola_efficienza_secondo_piano(self) -> Dict:
        """Calcola l'efficienza dell'utilizzo del secondo piano"""
        total_nesting = self.statistiche_globali["nesting_creati"]
        utilizzo_secondo_piano = self.statistiche_globali["utilizzo_secondo_piano"]
        
        return {
            "nesting_con_secondo_piano": utilizzo_secondo_piano,
            "percentuale_utilizzo": round((utilizzo_secondo_piano / total_nesting * 100), 2) if total_nesting > 0 else 0
        }
    
    def _genera_raccomandazioni(self) -> List[str]:
        """Genera raccomandazioni basate sui risultati del test"""
        raccomandazioni = []
        
        # Analizza tasso di successo
        prestazioni = self._analizza_prestazioni()
        tasso_successo = prestazioni.get("tasso_successo_percentuale", 0)
        
        if tasso_successo < 70:
            raccomandazioni.append("⚠️ Tasso di successo basso (<70%). Considerare ottimizzazione parametri algoritmo.")
        
        if tasso_successo > 90:
            raccomandazioni.append("✅ Ottimo tasso di successo (>90%). Algoritmo ben configurato.")
        
        # Analizza errori
        if self.statistiche_globali["errori_algoritmo"]:
            raccomandazioni.append("❌ Rilevati errori nell'algoritmo. Verificare implementazione OR-Tools.")
        
        # Analizza utilizzo secondo piano
        if self.statistiche_globali["utilizzo_secondo_piano"] == 0:
            raccomandazioni.append("📋 Secondo piano mai utilizzato. Verificare logica di assegnazione.")
        
        # Analizza scarto ODL
        tasso_scarto = prestazioni.get("tasso_scarto_percentuale", 0)
        if tasso_scarto > 30:
            raccomandazioni.append("⚠️ Alto tasso di scarto ODL (>30%). Migliorare validazione dati input.")
        
        return raccomandazioni
    
    def _stampa_riassunto_finale(self):
        """Stampa un riassunto finale dei risultati"""
        print("\n" + "="*80)
        print("🧪 RIASSUNTO FINALE STRESS TEST NESTING")
        print("="*80)
        
        print(f"📊 STATISTICHE GLOBALI:")
        print(f"   • Iterazioni completate: {len(self.risultati_test)}")
        print(f"   • Nesting creati: {self.statistiche_globali['nesting_creati']}")
        print(f"   • Nesting falliti: {self.statistiche_globali['nesting_falliti']}")
        print(f"   • ODL assegnati: {self.statistiche_globali['odl_assegnati']}")
        print(f"   • ODL scartati: {self.statistiche_globali['odl_scartati']}")
        print(f"   • Utilizzo secondo piano: {self.statistiche_globali['utilizzo_secondo_piano']} volte")
        
        prestazioni = self._analizza_prestazioni()
        print(f"\n📈 PRESTAZIONI:")
        print(f"   • Tasso successo: {prestazioni.get('tasso_successo_percentuale', 0)}%")
        print(f"   • Tasso scarto: {prestazioni.get('tasso_scarto_percentuale', 0)}%")
        print(f"   • Utilizzo medio autoclavi: {prestazioni.get('utilizzo_medio_autoclavi', 0)}%")
        
        if self.statistiche_globali["errori_algoritmo"]:
            print(f"\n❌ ERRORI RILEVATI:")
            for errore in self.statistiche_globali["errori_algoritmo"][:5]:  # Mostra solo i primi 5
                print(f"   • {errore}")
        
        print("\n" + "="*80)
    
    def esegui_stress_test_completo(self):
        """
        🚀 ESECUZIONE STRESS TEST COMPLETO
        Metodo principale che coordina tutto il test
        """
        logger.info("🚀 Inizio stress test completo nesting...")
        logger.info(f"📋 Configurazione: {self.config.num_iterazioni} iterazioni, {self.config.num_odl_per_iterazione} ODL per iterazione")
        
        try:
            for iterazione in range(1, self.config.num_iterazioni + 1):
                logger.info(f"\n🔄 ITERAZIONE #{iterazione}/{self.config.num_iterazioni}")
                
                # 1. Pulizia database
                self.pulisci_database_completo()
                
                # 2. Creazione seed dati
                autoclavi, odl_list = self.crea_seed_dati_realistici(iterazione)
                
                # 3. Test nesting
                risultato = self.esegui_test_nesting(iterazione, autoclavi, odl_list)
                self.risultati_test.append(risultato)
                
                # 4. Log risultati iterazione
                logger.info(f"✅ Iterazione #{iterazione} completata:")
                logger.info(f"   • Nesting creati: {len(risultato['nesting_creati'])}")
                logger.info(f"   • ODL assegnati: {len(risultato['odl_assegnati'])}")
                logger.info(f"   • ODL scartati: {len(risultato['odl_scartati'])}")
                
                if risultato["utilizzo_secondo_piano"]:
                    logger.info(f"   • Secondo piano utilizzato su autoclavi: {risultato['utilizzo_secondo_piano']}")
            
            # 5. Generazione report finale
            nome_report = self.genera_report_finale()
            
            logger.info("🎯 Stress test completato con successo!")
            return nome_report
            
        except Exception as e:
            logger.error(f"❌ Errore durante stress test: {str(e)}")
            raise

def main():
    """Funzione principale per eseguire lo stress test"""
    print("🧪 STRESS TEST NESTING + VALIDAZIONE OR-TOOLS")
    print("=" * 50)
    
    # Configurazione test
    config = TestConfig(
        num_iterazioni=3,
        num_odl_per_iterazione=12,
        percentuale_odl_validi=0.6,
        percentuale_odl_borderline=0.3,
        percentuale_odl_errati=0.1,
        abilita_secondo_piano=True,
        log_dettagliato=True
    )
    
    # Esecuzione test
    with StressTestNesting(config) as test:
        nome_report = test.esegui_stress_test_completo()
        print(f"\n📄 Report finale salvato in: {nome_report}")

if __name__ == "__main__":
    main() 