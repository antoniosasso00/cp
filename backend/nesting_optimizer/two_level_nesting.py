"""
Algoritmo di nesting su due piani ottimizzato per peso e dimensione.
Posiziona i pezzi più pesanti e grandi nel piano inferiore,
i pezzi più leggeri e piccoli nel piano superiore.
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from models.odl import ODL
from models.autoclave import Autoclave
from models.nesting_result import NestingResult as NestingResultModel
import logging

logger = logging.getLogger(__name__)

class TwoLevelNestingResult:
    """Classe per contenere il risultato dell'ottimizzazione di nesting su due piani"""
    
    def __init__(self):
        # Assegnamenti per piano: piano_id -> [odl_ids]
        self.piano_1: List[int] = []  # Piano inferiore (pezzi pesanti/grandi)
        self.piano_2: List[int] = []  # Piano superiore (pezzi leggeri/piccoli)
        
        # ODL non assegnabili con motivazioni
        self.odl_non_pianificabili: List[Dict] = []
        
        # Statistiche per piano
        self.peso_piano_1: float = 0.0
        self.peso_piano_2: float = 0.0
        self.area_piano_1: float = 0.0
        self.area_piano_2: float = 0.0
        
        # Posizioni 2D per ogni piano
        self.posizioni_piano_1: List[Dict] = []
        self.posizioni_piano_2: List[Dict] = []
        
        # Validazione carico
        self.peso_totale: float = 0.0
        self.carico_valido: bool = True
        self.motivo_invalidita: str = ""
    
    def aggiungi_al_piano_1(self, odl_id: int, peso: float, area: float, posizione: Optional[Dict] = None):
        """Aggiunge un ODL al piano 1 (inferiore)"""
        self.piano_1.append(odl_id)
        self.peso_piano_1 += peso
        self.area_piano_1 += area
        self.peso_totale += peso
        
        if posizione:
            self.posizioni_piano_1.append({
                "odl_id": odl_id,
                "piano": 1,
                "x": posizione.get("x", 0),
                "y": posizione.get("y", 0),
                "width": posizione.get("width", 0),
                "height": posizione.get("height", 0)
            })
    
    def aggiungi_al_piano_2(self, odl_id: int, peso: float, area: float, posizione: Optional[Dict] = None):
        """Aggiunge un ODL al piano 2 (superiore)"""
        self.piano_2.append(odl_id)
        self.peso_piano_2 += peso
        self.area_piano_2 += area
        self.peso_totale += peso
        
        if posizione:
            self.posizioni_piano_2.append({
                "odl_id": odl_id,
                "piano": 2,
                "x": posizione.get("x", 0),
                "y": posizione.get("y", 0),
                "width": posizione.get("width", 0),
                "height": posizione.get("height", 0)
            })
    
    def aggiungi_non_pianificabile(self, odl_id: int, motivo: str):
        """Aggiunge un ODL alla lista di quelli non pianificabili"""
        self.odl_non_pianificabili.append({
            "odl_id": odl_id,
            "motivo": motivo
        })
    
    def valida_carico(self, max_load_kg: float):
        """Valida che il carico totale non superi il limite dell'autoclave"""
        if self.peso_totale > max_load_kg:
            self.carico_valido = False
            self.motivo_invalidita = f"Carico totale ({self.peso_totale:.2f}kg) supera il limite dell'autoclave ({max_load_kg}kg)"
        else:
            self.carico_valido = True
            self.motivo_invalidita = ""

def validate_odl_for_two_level_nesting(db: Session, odl: ODL) -> Tuple[bool, str, Dict]:
    """
    Valida se un ODL può essere incluso nel nesting su due piani
    
    Args:
        db: Sessione del database
        odl: ODL da validare
        
    Returns:
        Tupla (is_valid, error_message, data_dict)
    """
    try:
        # Verifica che l'ODL abbia una parte associata
        if not odl.parte:
            return False, "ODL senza parte associata", {}
        
        parte = odl.parte
        
        # Verifica che la parte abbia un catalogo associato
        if not parte.catalogo:
            return False, "Parte senza catalogo associato", {}
        
        catalogo = parte.catalogo
        
        # Verifica che l'ODL abbia un tool associato
        if not odl.tool:
            return False, "ODL senza tool associato", {}
        
        tool = odl.tool
        
        # Verifica che il catalogo abbia le informazioni necessarie
        if not catalogo.area_cm2 or catalogo.area_cm2 <= 0:
            return False, "Area della parte non definita o non valida", {}
        
        # Verifica che il tool abbia dimensioni valide
        if not tool.lunghezza_piano or tool.lunghezza_piano <= 0:
            return False, "Lunghezza piano del tool non definita o non valida", {}
        
        if not tool.larghezza_piano or tool.larghezza_piano <= 0:
            return False, "Larghezza piano del tool non definita o non valida", {}
        
        # Verifica che la parte abbia il numero di valvole richieste
        if not parte.num_valvole_richieste or parte.num_valvole_richieste <= 0:
            return False, "Numero di valvole richieste non definito", {}
        
        # Verifica che la parte abbia un ciclo di cura associato
        if not parte.ciclo_cura_id:
            return False, "Parte senza ciclo di cura associato", {}
        
        # Verifica che l'ODL non sia già in un nesting attivo
        existing_nesting = db.query(NestingResultModel).filter(
            NestingResultModel.odl_ids.contains([odl.id]),
            NestingResultModel.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
        ).first()
        
        if existing_nesting:
            return False, f"ODL già incluso nel nesting #{existing_nesting.id}", {}
        
        # Prepara i dati dell'ODL per l'ottimizzazione
        data = {
            "area_cm2": float(catalogo.area_cm2),
            "num_valvole": int(parte.num_valvole_richieste),
            "priorita": int(odl.priorita) if odl.priorita else 1,
            "part_number": catalogo.part_number,
            "descrizione": parte.descrizione_breve or "Sconosciuta",
            "ciclo_cura_id": parte.ciclo_cura_id,
            "ciclo_cura_nome": parte.ciclo_cura.nome if parte.ciclo_cura else "Sconosciuto",
            # Dimensioni reali del tool
            "tool_lunghezza_mm": float(tool.lunghezza_piano),
            "tool_larghezza_mm": float(tool.larghezza_piano),
            "tool_area_cm2": float(tool.area),
            "tool_peso_kg": float(tool.peso) if tool.peso else 0.0,
            "tool_materiale": tool.materiale or "Sconosciuto",
            "tool_part_number": tool.part_number_tool,
            "tool_descrizione": tool.descrizione or "Sconosciuta"
        }
        
        return True, "", data
        
    except Exception as e:
        logger.error(f"Errore nella validazione ODL {odl.id}: {str(e)}")
        return False, f"Errore nella validazione ODL: {str(e)}", {}

def calculate_weight_priority_score(peso_kg: float, area_cm2: float) -> float:
    """
    Calcola un punteggio di priorità basato su peso e area per ordinare i tool.
    Punteggio più alto = priorità più alta per il piano inferiore.
    
    Args:
        peso_kg: Peso del tool in kg
        area_cm2: Area del tool in cm²
        
    Returns:
        Punteggio di priorità (float)
    """
    # Normalizzazione: peso ha peso maggiore (70%) rispetto all'area (30%)
    peso_normalizzato = peso_kg * 0.7
    area_normalizzata = (area_cm2 / 100) * 0.3  # Diviso 100 per ridurre l'impatto dell'area
    
    return peso_normalizzato + area_normalizzata

def calculate_2d_positioning_two_levels(
    odl_data_piano_1: List[Dict], 
    odl_data_piano_2: List[Dict],
    autoclave_width_mm: float, 
    autoclave_height_mm: float,
    superficie_piano_2_max_cm2: Optional[float] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Calcola il posizionamento 2D per entrambi i piani dell'autoclave
    
    Args:
        odl_data_piano_1: Lista dei dati degli ODL per il piano 1
        odl_data_piano_2: Lista dei dati degli ODL per il piano 2
        autoclave_width_mm: Larghezza del piano autoclave in mm
        autoclave_height_mm: Lunghezza del piano autoclave in mm
        superficie_piano_2_max_cm2: Superficie massima del piano 2 in cm²
        
    Returns:
        Tupla (posizioni_piano_1, posizioni_piano_2)
    """
    
    def position_tools_on_plane(odl_data: List[Dict], plane_width_mm: float, plane_height_mm: float) -> List[Dict]:
        """Posiziona i tool su un singolo piano"""
        positioned_tools = []
        
        # Ordina per area decrescente (strategia First Fit Decreasing)
        sorted_odl_data = sorted(
            enumerate(odl_data), 
            key=lambda x: x[1]["tool_lunghezza_mm"] * x[1]["tool_larghezza_mm"], 
            reverse=True
        )
        
        # Margine di sicurezza tra i tool (5mm)
        MARGIN_MM = 5.0
        
        # Lista delle aree occupate: [(x, y, width, height), ...]
        occupied_areas = []
        
        def check_overlap(x, y, width, height, occupied_areas):
            """Verifica se una posizione si sovrappone con aree già occupate"""
            for ox, oy, ow, oh in occupied_areas:
                if not (x >= ox + ow + MARGIN_MM or 
                       x + width + MARGIN_MM <= ox or 
                       y >= oy + oh + MARGIN_MM or 
                       y + height + MARGIN_MM <= oy):
                    return True
            return False
        
        def find_position(width, height, plane_width, plane_height, occupied_areas):
            """Trova la prima posizione disponibile per un tool"""
            step = 10.0  # Step di 10mm per efficienza
            
            for y in range(0, int(plane_height - height + 1), int(step)):
                for x in range(0, int(plane_width - width + 1), int(step)):
                    if not check_overlap(x, y, width, height, occupied_areas):
                        return x, y
            return None, None
        
        # Posiziona ogni tool
        for original_index, data in sorted_odl_data:
            tool_width = data["tool_lunghezza_mm"]
            tool_height = data["tool_larghezza_mm"]
            
            # Trova posizione disponibile
            x, y = find_position(tool_width, tool_height, plane_width_mm, plane_height_mm, occupied_areas)
            
            if x is not None and y is not None:
                # Posizione trovata
                positioned_tools.append({
                    "odl_id": data.get("odl_id"),
                    "x": x,
                    "y": y,
                    "width": tool_width,
                    "height": tool_height
                })
                
                # Aggiungi area occupata
                occupied_areas.append((x, y, tool_width, tool_height))
            else:
                # Nessuna posizione disponibile
                logger.warning(f"Impossibile posizionare tool ODL {data.get('odl_id')} sul piano")
        
        return positioned_tools
    
    # Calcola dimensioni piano 2 se specificata superficie massima
    piano_2_width_mm = autoclave_width_mm
    piano_2_height_mm = autoclave_height_mm
    
    if superficie_piano_2_max_cm2:
        # Converti cm² in mm²
        superficie_piano_2_max_mm2 = superficie_piano_2_max_cm2 * 100
        
        # Mantieni proporzioni dell'autoclave ma riduci l'area
        ratio = (superficie_piano_2_max_mm2 / (autoclave_width_mm * autoclave_height_mm)) ** 0.5
        piano_2_width_mm = autoclave_width_mm * ratio
        piano_2_height_mm = autoclave_height_mm * ratio
    
    # Posiziona tool sui due piani
    posizioni_piano_1 = position_tools_on_plane(odl_data_piano_1, autoclave_width_mm, autoclave_height_mm)
    posizioni_piano_2 = position_tools_on_plane(odl_data_piano_2, piano_2_width_mm, piano_2_height_mm)
    
    return posizioni_piano_1, posizioni_piano_2

def compute_two_level_nesting(
    db: Session,
    odl_list: List[ODL],
    autoclave: Autoclave,
    superficie_piano_2_max_cm2: Optional[float] = None
) -> TwoLevelNestingResult:
    """
    Calcola il nesting ottimizzato su due piani per un'autoclave
    
    Args:
        db: Sessione del database
        odl_list: Lista degli ODL da processare
        autoclave: Autoclave target
        superficie_piano_2_max_cm2: Superficie massima del piano 2 in cm²
        
    Returns:
        TwoLevelNestingResult con i risultati dell'ottimizzazione
    """
    result = TwoLevelNestingResult()
    
    # Valida e prepara i dati degli ODL
    odl_validi = []
    odl_data = []
    
    for odl in odl_list:
        is_valid, error_msg, data = validate_odl_for_two_level_nesting(db, odl)
        
        if is_valid:
            data["odl_id"] = odl.id
            odl_validi.append(odl)
            odl_data.append(data)
        else:
            result.aggiungi_non_pianificabile(odl.id, error_msg)
    
    if not odl_validi:
        logger.warning("Nessun ODL valido per il nesting")
        return result
    
    # Ordina gli ODL per priorità peso/area (decrescente)
    odl_con_priorita = []
    for i, data in enumerate(odl_data):
        peso = data["tool_peso_kg"]
        area = data["tool_area_cm2"]
        priorita_score = calculate_weight_priority_score(peso, area)
        
        odl_con_priorita.append({
            "index": i,
            "odl_id": data["odl_id"],
            "data": data,
            "priorita_score": priorita_score,
            "peso": peso,
            "area": area
        })
    
    # Ordina per priorità decrescente (pezzi più pesanti/grandi prima)
    odl_con_priorita.sort(key=lambda x: x["priorita_score"], reverse=True)
    
    # Calcola area disponibile per ogni piano
    area_piano_1_max = autoclave.area_piano  # Area completa dell'autoclave
    area_piano_2_max = superficie_piano_2_max_cm2 or (area_piano_1_max * 0.8)  # Default: 80% del piano 1
    
    area_piano_1_utilizzata = 0.0
    area_piano_2_utilizzata = 0.0
    
    # Assegna ODL ai piani
    for item in odl_con_priorita:
        odl_id = item["odl_id"]
        data = item["data"]
        peso = item["peso"]
        area = item["area"]
        
        # Strategia di assegnazione:
        # 1. Pezzi pesanti (>= soglia peso) vanno al piano 1
        # 2. Se piano 1 è pieno, pezzi leggeri vanno al piano 2
        # 3. Se entrambi i piani sono pieni, ODL non pianificabile
        
        SOGLIA_PESO_KG = 5.0  # Soglia per considerare un pezzo "pesante"
        
        if peso >= SOGLIA_PESO_KG or len(result.piano_2) == 0:
            # Prova ad assegnare al piano 1
            if area_piano_1_utilizzata + area <= area_piano_1_max:
                result.aggiungi_al_piano_1(odl_id, peso, area)
                area_piano_1_utilizzata += area
            elif area_piano_2_utilizzata + area <= area_piano_2_max:
                # Piano 1 pieno, prova piano 2
                result.aggiungi_al_piano_2(odl_id, peso, area)
                area_piano_2_utilizzata += area
            else:
                # Entrambi i piani pieni
                result.aggiungi_non_pianificabile(odl_id, "Spazio insufficiente su entrambi i piani")
        else:
            # Pezzo leggero, prova prima piano 2
            if area_piano_2_utilizzata + area <= area_piano_2_max:
                result.aggiungi_al_piano_2(odl_id, peso, area)
                area_piano_2_utilizzata += area
            elif area_piano_1_utilizzata + area <= area_piano_1_max:
                # Piano 2 pieno, prova piano 1
                result.aggiungi_al_piano_1(odl_id, peso, area)
                area_piano_1_utilizzata += area
            else:
                # Entrambi i piani pieni
                result.aggiungi_non_pianificabile(odl_id, "Spazio insufficiente su entrambi i piani")
    
    # Valida il carico totale
    max_load_kg = autoclave.max_load_kg or 1000.0
    result.valida_carico(max_load_kg)
    
    # Calcola posizioni 2D se ci sono ODL assegnati
    if result.piano_1 or result.piano_2:
        # Prepara dati per posizionamento
        odl_data_piano_1 = [data for data in odl_data if data["odl_id"] in result.piano_1]
        odl_data_piano_2 = [data for data in odl_data if data["odl_id"] in result.piano_2]
        
        posizioni_1, posizioni_2 = calculate_2d_positioning_two_levels(
            odl_data_piano_1,
            odl_data_piano_2,
            autoclave.larghezza_piano,
            autoclave.lunghezza,
            superficie_piano_2_max_cm2
        )
        
        result.posizioni_piano_1 = posizioni_1
        result.posizioni_piano_2 = posizioni_2
    
    logger.info(f"Nesting completato: Piano 1: {len(result.piano_1)} ODL ({result.peso_piano_1:.2f}kg), "
                f"Piano 2: {len(result.piano_2)} ODL ({result.peso_piano_2:.2f}kg), "
                f"Non pianificabili: {len(result.odl_non_pianificabili)}")
    
    return result 