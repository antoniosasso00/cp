"""
Servizio di ottimizzazione per il nesting automatico multi-autoclave.
Implementa algoritmi di ottimizzazione per distribuire ODL su più autoclavi.
"""

from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
import logging
import math
from datetime import datetime

# Importazioni dei modelli
from models import ODL, Autoclave, Tool, CicloCura

# Configurazione logging
logger = logging.getLogger(__name__)


class NestingOptimizerService:
    """
    Servizio per l'ottimizzazione del nesting automatico multi-autoclave.
    
    Implementa algoritmi di ottimizzazione per:
    - Distribuzione ottimale degli ODL su più autoclavi
    - Massimizzazione dell'efficienza di utilizzo
    - Separazione per cicli di cura compatibili
    - Gestione dei vincoli di peso e dimensioni
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ottimizza_multi_autoclave(
        self,
        odl_list: List[ODL],
        autoclavi: List[Autoclave],
        parametri: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Ottimizza la distribuzione degli ODL su più autoclavi.
        
        Args:
            odl_list: Lista degli ODL da distribuire
            autoclavi: Lista delle autoclavi disponibili
            parametri: Parametri di ottimizzazione
            
        Returns:
            Dict contenente i risultati dell'ottimizzazione
        """
        self.logger.info(f"Inizio ottimizzazione multi-autoclave per {len(odl_list)} ODL su {len(autoclavi)} autoclavi")
        
        # Parametri di default
        parametri_default = {
            "efficienza_minima_percent": 60.0,
            "peso_massimo_percent": 90.0,
            "margine_sicurezza_mm": 10.0,
            "priorita_efficienza": True,
            "separa_cicli_cura": True
        }
        parametri_finali = {**parametri_default, **(parametri or {})}
        
        try:
            # 1. Raggruppa ODL per ciclo di cura se richiesto
            if parametri_finali["separa_cicli_cura"]:
                gruppi_cicli = self._raggruppa_per_ciclo_cura(odl_list)
            else:
                gruppi_cicli = {"tutti": odl_list}
            
            # 2. Per ogni gruppo di ciclo, ottimizza la distribuzione
            risultati_nesting = []
            odl_processati = set()
            
            for ciclo_nome, odl_gruppo in gruppi_cicli.items():
                self.logger.info(f"Processando gruppo '{ciclo_nome}' con {len(odl_gruppo)} ODL")
                
                # Filtra ODL non ancora processati
                odl_da_processare = [odl for odl in odl_gruppo if odl.id not in odl_processati]
                
                if not odl_da_processare:
                    continue
                
                # Ottimizza per questo gruppo
                risultati_gruppo = self._ottimizza_gruppo_ciclo(
                    odl_da_processare, 
                    autoclavi, 
                    parametri_finali
                )
                
                risultati_nesting.extend(risultati_gruppo)
                
                # Segna ODL come processati
                for risultato in risultati_gruppo:
                    for odl in risultato["odl_assegnati"]:
                        odl_processati.add(odl["id"])
            
            # 3. Calcola statistiche globali
            statistiche_globali = self._calcola_statistiche_globali(risultati_nesting, odl_list)
            
            # 4. Prepara il risultato finale
            risultato_finale = {
                "success": True,
                "nesting_results": risultati_nesting,
                "statistiche_globali": statistiche_globali,
                "parametri_utilizzati": parametri_finali,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Ottimizzazione completata: {len(risultati_nesting)} autoclavi utilizzate")
            return risultato_finale
            
        except Exception as e:
            self.logger.error(f"Errore durante l'ottimizzazione: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "nesting_results": [],
                "statistiche_globali": {},
                "parametri_utilizzati": parametri_finali
            }
    
    def _raggruppa_per_ciclo_cura(self, odl_list: List[ODL]) -> Dict[str, List[ODL]]:
        """
        Raggruppa gli ODL per ciclo di cura compatibile.
        """
        gruppi = {}
        
        for odl in odl_list:
            if odl.parte and odl.parte.ciclo_cura:
                ciclo_nome = odl.parte.ciclo_cura.nome
            else:
                ciclo_nome = "senza_ciclo"
            
            if ciclo_nome not in gruppi:
                gruppi[ciclo_nome] = []
            gruppi[ciclo_nome].append(odl)
        
        self.logger.info(f"Creati {len(gruppi)} gruppi per ciclo di cura")
        return gruppi
    
    def _ottimizza_gruppo_ciclo(
        self,
        odl_gruppo: List[ODL],
        autoclavi: List[Autoclave],
        parametri: Dict
    ) -> List[Dict]:
        """
        Ottimizza la distribuzione di un gruppo di ODL con lo stesso ciclo di cura.
        """
        risultati = []
        odl_rimanenti = odl_gruppo.copy()
        autoclavi_utilizzate = set()
        
        # Ordina ODL per priorità e dimensioni (più grandi prima)
        odl_rimanenti.sort(key=lambda x: (
            -self._get_priorita_numerica(x.priorita),
            -self._calcola_area_tool(x.tool) if x.tool else 0
        ))
        
        while odl_rimanenti and len(autoclavi_utilizzate) < len(autoclavi):
            # Trova la migliore autoclave per gli ODL rimanenti
            migliore_risultato = self._trova_migliore_autoclave(
                odl_rimanenti, 
                autoclavi, 
                autoclavi_utilizzate, 
                parametri
            )
            
            if migliore_risultato:
                risultati.append(migliore_risultato)
                autoclavi_utilizzate.add(migliore_risultato["autoclave_id"])
                
                # Rimuovi ODL assegnati
                odl_assegnati_ids = [odl["id"] for odl in migliore_risultato["odl_assegnati"]]
                odl_rimanenti = [odl for odl in odl_rimanenti if odl.id not in odl_assegnati_ids]
                
                self.logger.debug(f"Assegnata autoclave {migliore_risultato['autoclave_id']}, "
                                f"rimangono {len(odl_rimanenti)} ODL")
            else:
                # Nessuna autoclave può ospitare gli ODL rimanenti
                self.logger.warning(f"Impossibile assegnare {len(odl_rimanenti)} ODL rimanenti")
                break
        
        return risultati
    
    def _trova_migliore_autoclave(
        self,
        odl_list: List[ODL],
        autoclavi: List[Autoclave],
        autoclavi_utilizzate: set,
        parametri: Dict
    ) -> Optional[Dict]:
        """
        Trova la migliore autoclave per un set di ODL.
        """
        self.logger.info(f"_trova_migliore_autoclave: {len(odl_list)} ODL, {len(autoclavi)} autoclavi, {len(autoclavi_utilizzate)} già utilizzate")
        
        migliore_risultato = None
        migliore_score = 0
        
        for autoclave in autoclavi:
            if autoclave.id in autoclavi_utilizzate:
                self.logger.debug(f"Autoclave {autoclave.id} ({autoclave.nome}) già utilizzata, skip")
                continue
            
            self.logger.debug(f"Testando autoclave {autoclave.id} ({autoclave.nome})")
            
            # Simula il nesting per questa autoclave
            risultato = self._simula_nesting_autoclave(odl_list, autoclave, parametri)
            
            if risultato:
                self.logger.debug(f"Autoclave {autoclave.id}: {len(risultato['odl_assegnati'])} ODL assegnati")
                score = self._calcola_score_autoclave(risultato, parametri)
                
                if score > migliore_score:
                    migliore_risultato = risultato
                    migliore_score = score
                    self.logger.debug(f"Nuovo migliore risultato: autoclave {autoclave.id}, score {score}")
            else:
                self.logger.debug(f"Autoclave {autoclave.id}: nessun ODL assegnabile")
        
        if migliore_risultato:
            self.logger.info(f"Migliore autoclave trovata: {migliore_risultato['autoclave_id']} con {len(migliore_risultato['odl_assegnati'])} ODL")
        else:
            self.logger.warning("Nessuna autoclave valida trovata per gli ODL forniti")
        
        return migliore_risultato
    
    def _simula_nesting_autoclave(
        self,
        odl_list: List[ODL],
        autoclave: Autoclave,
        parametri: Dict
    ) -> Optional[Dict]:
        """
        Simula il nesting degli ODL in una specifica autoclave.
        """
        try:
            self.logger.debug(f"_simula_nesting_autoclave: autoclave {autoclave.id} ({autoclave.nome}), {len(odl_list)} ODL")
            
            # Dimensioni autoclave (converti da mm a cm per calcoli)
            larghezza_autoclave = autoclave.larghezza_piano / 10  # mm -> cm
            lunghezza_autoclave = autoclave.lunghezza / 10  # mm -> cm
            area_totale = larghezza_autoclave * lunghezza_autoclave
            
            self.logger.debug(f"Dimensioni autoclave: {lunghezza_autoclave:.1f}x{larghezza_autoclave:.1f} cm (area: {area_totale:.1f} cm²)")
            
            # Capacità peso
            capacita_peso = autoclave.max_load_kg or 1000  # Default 1000kg
            peso_massimo = capacita_peso * (parametri["peso_massimo_percent"] / 100)
            
            self.logger.debug(f"Peso massimo consentito: {peso_massimo:.1f} kg ({parametri['peso_massimo_percent']}% di {capacita_peso} kg)")
            
            # Algoritmo di nesting semplificato (First Fit Decreasing)
            odl_assegnati = []
            posizioni_tool = []
            peso_totale = 0
            area_utilizzata_piano_1 = 0
            area_utilizzata_piano_2 = 0
            
            # Ordina ODL per area decrescente
            odl_ordinati = sorted(odl_list, key=lambda x: -self._calcola_area_tool(x.tool) if x.tool else 0)
            
            # Griglia per tracciare le posizioni occupate (semplificata)
            griglia_piano_1 = self._crea_griglia(larghezza_autoclave, lunghezza_autoclave)
            griglia_piano_2 = self._crea_griglia(larghezza_autoclave, lunghezza_autoclave) if autoclave.use_secondary_plane else None
            
            self.logger.debug(f"Griglia piano 1: {len(griglia_piano_1)}x{len(griglia_piano_1[0]) if griglia_piano_1 else 0} celle")
            if griglia_piano_2:
                self.logger.debug(f"Griglia piano 2: {len(griglia_piano_2)}x{len(griglia_piano_2[0]) if griglia_piano_2 else 0} celle")
            
            for i, odl in enumerate(odl_ordinati):
                if not odl.tool:
                    self.logger.debug(f"ODL {odl.id}: nessun tool associato, skip")
                    continue
                
                tool = odl.tool
                peso_tool = tool.peso or 0
                
                # Verifica vincolo peso
                if peso_totale + peso_tool > peso_massimo:
                    self.logger.debug(f"ODL {odl.id}: peso {peso_tool} kg supererebbe limite ({peso_totale + peso_tool:.1f} > {peso_massimo:.1f}), skip")
                    continue
                
                # Dimensioni tool (mm -> cm)
                larghezza_tool = tool.larghezza_piano / 10 if tool.larghezza_piano else 0
                lunghezza_tool = tool.lunghezza_piano / 10 if tool.lunghezza_piano else 0
                
                if larghezza_tool <= 0 or lunghezza_tool <= 0:
                    self.logger.debug(f"ODL {odl.id}: dimensioni tool non valide ({lunghezza_tool:.1f}x{larghezza_tool:.1f} cm), skip")
                    continue
                
                area_tool = larghezza_tool * lunghezza_tool
                self.logger.debug(f"ODL {odl.id}: tool {lunghezza_tool:.1f}x{larghezza_tool:.1f} cm, area {area_tool:.1f} cm², peso {peso_tool} kg")
                
                # Prova a posizionare sul piano 1
                posizione = self._trova_posizione_libera(
                    griglia_piano_1, larghezza_tool, lunghezza_tool, 
                    larghezza_autoclave, lunghezza_autoclave, parametri["margine_sicurezza_mm"] / 10
                )
                
                piano_assegnato = 1
                
                # Se non entra nel piano 1, prova piano 2
                if not posizione and griglia_piano_2:
                    self.logger.debug(f"ODL {odl.id}: non entra nel piano 1, provo piano 2")
                    posizione = self._trova_posizione_libera(
                        griglia_piano_2, larghezza_tool, lunghezza_tool,
                        larghezza_autoclave, lunghezza_autoclave, parametri["margine_sicurezza_mm"] / 10
                    )
                    piano_assegnato = 2
                
                if posizione:
                    self.logger.debug(f"ODL {odl.id}: assegnato al piano {piano_assegnato} in posizione ({posizione[0]:.1f}, {posizione[1]:.1f}) cm")
                    
                    # Assegna il tool
                    odl_assegnati.append({
                        "id": odl.id,
                        "numero_odl": f"ODL-{odl.id:06d}",
                        "tool_nome": tool.part_number_tool,
                        "peso_kg": peso_tool
                    })
                    
                    posizioni_tool.append({
                        "odl_id": odl.id,
                        "piano": piano_assegnato,
                        "x": posizione[0] * 10,  # cm -> mm
                        "y": posizione[1] * 10,  # cm -> mm
                        "width": larghezza_tool * 10,  # cm -> mm
                        "height": lunghezza_tool * 10  # cm -> mm
                    })
                    
                    peso_totale += peso_tool
                    
                    if piano_assegnato == 1:
                        area_utilizzata_piano_1 += area_tool
                        self._occupa_griglia(griglia_piano_1, posizione, larghezza_tool, lunghezza_tool)
                    else:
                        area_utilizzata_piano_2 += area_tool
                        self._occupa_griglia(griglia_piano_2, posizione, larghezza_tool, lunghezza_tool)
                else:
                    self.logger.debug(f"ODL {odl.id}: nessuna posizione libera trovata")
            
            # Calcola statistiche
            area_totale_utilizzata = area_utilizzata_piano_1 + area_utilizzata_piano_2
            efficienza_totale = (area_totale_utilizzata / area_totale) * 100 if area_totale > 0 else 0
            
            self.logger.debug(f"Risultato simulazione: {len(odl_assegnati)} ODL assegnati, efficienza {efficienza_totale:.1f}%")
            
            # Verifica efficienza minima
            if efficienza_totale < parametri["efficienza_minima_percent"]:
                self.logger.debug(f"Efficienza {efficienza_totale:.1f}% sotto il minimo {parametri['efficienza_minima_percent']}%, scarto risultato")
                return None
            
            return {
                "autoclave_id": autoclave.id,
                "odl_assegnati": odl_assegnati,
                "posizioni_tool": posizioni_tool,
                "statistiche": {
                    "area_utilizzata": area_totale_utilizzata,
                    "area_totale": area_totale,
                    "peso_totale": peso_totale,
                    "area_piano_1": area_utilizzata_piano_1,
                    "area_piano_2": area_utilizzata_piano_2,
                    "superficie_piano_2_max": autoclave.area_piano / 2 if autoclave.use_secondary_plane else 0,
                    "efficienza_totale": efficienza_totale,
                    "numero_odl": len(odl_assegnati)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Errore nella simulazione nesting per autoclave {autoclave.id}: {str(e)}")
            return None
    
    def _crea_griglia(self, larghezza: float, lunghezza: float, risoluzione: float = 1.0) -> List[List[bool]]:
        """
        Crea una griglia per tracciare le posizioni occupate.
        """
        righe = int(lunghezza / risoluzione)
        colonne = int(larghezza / risoluzione)
        return [[False for _ in range(colonne)] for _ in range(righe)]
    
    def _trova_posizione_libera(
        self,
        griglia: List[List[bool]],
        larghezza_tool: float,
        lunghezza_tool: float,
        larghezza_max: float,
        lunghezza_max: float,
        margine: float = 1.0
    ) -> Optional[Tuple[float, float]]:
        """
        Trova una posizione libera nella griglia per il tool.
        """
        risoluzione = 1.0  # cm
        
        # Dimensioni in celle della griglia
        celle_larghezza = int(larghezza_tool / risoluzione) + int(margine / risoluzione)
        celle_lunghezza = int(lunghezza_tool / risoluzione) + int(margine / risoluzione)
        
        righe_griglia = len(griglia)
        colonne_griglia = len(griglia[0]) if griglia else 0
        
        # Cerca posizione libera
        for r in range(righe_griglia - celle_lunghezza + 1):
            for c in range(colonne_griglia - celle_larghezza + 1):
                if self._posizione_libera(griglia, r, c, celle_lunghezza, celle_larghezza):
                    return (c * risoluzione, r * risoluzione)
        
        return None
    
    def _posizione_libera(
        self,
        griglia: List[List[bool]],
        riga: int,
        colonna: int,
        celle_lunghezza: int,
        celle_larghezza: int
    ) -> bool:
        """
        Verifica se una posizione è libera nella griglia.
        """
        for r in range(riga, riga + celle_lunghezza):
            for c in range(colonna, colonna + celle_larghezza):
                if r >= len(griglia) or c >= len(griglia[0]) or griglia[r][c]:
                    return False
        return True
    
    def _occupa_griglia(
        self,
        griglia: List[List[bool]],
        posizione: Tuple[float, float],
        larghezza_tool: float,
        lunghezza_tool: float
    ):
        """
        Marca come occupate le celle della griglia per un tool.
        """
        risoluzione = 1.0
        riga_start = int(posizione[1] / risoluzione)
        colonna_start = int(posizione[0] / risoluzione)
        celle_larghezza = int(larghezza_tool / risoluzione)
        celle_lunghezza = int(lunghezza_tool / risoluzione)
        
        for r in range(riga_start, min(riga_start + celle_lunghezza, len(griglia))):
            for c in range(colonna_start, min(colonna_start + celle_larghezza, len(griglia[0]))):
                griglia[r][c] = True
    
    def _calcola_score_autoclave(self, risultato: Dict, parametri: Dict) -> float:
        """
        Calcola uno score per valutare la qualità dell'assegnazione.
        """
        statistiche = risultato["statistiche"]
        
        # Fattori di score
        efficienza = statistiche["efficienza_totale"]
        numero_odl = statistiche["numero_odl"]
        utilizzo_peso = (statistiche["peso_totale"] / 1000) * 100  # Assumendo 1000kg max
        
        # Score pesato
        if parametri["priorita_efficienza"]:
            score = efficienza * 0.6 + numero_odl * 0.3 + utilizzo_peso * 0.1
        else:
            score = numero_odl * 0.5 + efficienza * 0.4 + utilizzo_peso * 0.1
        
        return score
    
    def _calcola_statistiche_globali(
        self,
        risultati_nesting: List[Dict],
        odl_originali: List[ODL]
    ) -> Dict:
        """
        Calcola le statistiche globali dell'ottimizzazione.
        """
        if not risultati_nesting:
            return {
                "autoclavi_utilizzate": 0,
                "odl_assegnati": 0,
                "odl_totali": len(odl_originali),
                "percentuale_assegnazione": 0.0,
                "efficienza_media": 0.0,
                "peso_totale": 0.0
            }
        
        # Conta ODL assegnati
        odl_assegnati_totali = sum(len(r["odl_assegnati"]) for r in risultati_nesting)
        
        # Calcola efficienza media
        efficienze = [r["statistiche"]["efficienza_totale"] for r in risultati_nesting]
        efficienza_media = sum(efficienze) / len(efficienze) if efficienze else 0
        
        # Calcola peso totale
        peso_totale = sum(r["statistiche"]["peso_totale"] for r in risultati_nesting)
        
        return {
            "autoclavi_utilizzate": len(risultati_nesting),
            "odl_assegnati": odl_assegnati_totali,
            "odl_totali": len(odl_originali),
            "percentuale_assegnazione": (odl_assegnati_totali / len(odl_originali)) * 100 if odl_originali else 0,
            "efficienza_media": efficienza_media,
            "peso_totale": peso_totale
        }
    
    def _get_priorita_numerica(self, priorita: str) -> int:
        """
        Converte la priorità testuale in valore numerico.
        """
        mapping = {
            "Alta": 3,
            "Media": 2,
            "Bassa": 1
        }
        return mapping.get(priorita, 1)
    
    def _calcola_area_tool(self, tool: Tool) -> float:
        """
        Calcola l'area di un tool in cm².
        """
        if not tool or not tool.larghezza_piano or not tool.lunghezza_piano:
            return 0
        return (tool.larghezza_piano * tool.lunghezza_piano) / 100  # mm² -> cm² 