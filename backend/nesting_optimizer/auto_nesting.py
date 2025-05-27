"""
Modulo per l'ottimizzazione del nesting automatico degli ODL nelle autoclavi
utilizzando Google OR-Tools con vincoli di posizionamento 2D reali.
"""

from typing import List, Dict, Tuple, Optional
from ortools.linear_solver import pywraplp
from sqlalchemy.orm import Session, joinedload
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.catalogo import Catalogo
import logging

# Configura il logger per il nesting
logger = logging.getLogger(__name__)

class NestingResult:
    """Classe per contenere il risultato dell'ottimizzazione di nesting"""
    
    def __init__(self):
        # Mappatura autoclave_id -> [odl_ids]
        self.assegnamenti: Dict[int, List[int]] = {}
        # Lista di ODL non assegnabili con motivazioni
        self.odl_non_pianificabili: List[Dict] = []
        # Statistiche sull'utilizzo delle autoclavi
        self.statistiche_autoclavi: Dict[int, Dict] = {}
        # Ciclo di cura assegnato per ogni autoclave
        self.cicli_cura_autoclavi: Dict[int, Dict] = {}
        # ✅ NUOVO: Posizioni 2D dei tool per ogni autoclave
        self.posizioni_tool: Dict[int, List[Dict]] = {}
        
    def aggiungi_assegnamento(self, autoclave_id: int, odl_id: int, posizione: Optional[Dict] = None):
        """Aggiunge un assegnamento di un ODL a un'autoclave con posizione opzionale"""
        if autoclave_id not in self.assegnamenti:
            self.assegnamenti[autoclave_id] = []
            self.posizioni_tool[autoclave_id] = []
        self.assegnamenti[autoclave_id].append(odl_id)
        
        # Aggiungi posizione se fornita
        if posizione:
            self.posizioni_tool[autoclave_id].append({
                "odl_id": odl_id,
                "x": posizione.get("x", 0),
                "y": posizione.get("y", 0),
                "width": posizione.get("width", 0),
                "height": posizione.get("height", 0)
            })
    
    def aggiungi_non_pianificabile(self, odl_id: int, motivo: str):
        """Aggiunge un ODL alla lista di quelli non pianificabili con motivazione"""
        self.odl_non_pianificabili.append({
            "odl_id": odl_id,
            "motivo": motivo
        })
        
    def imposta_statistiche_autoclave(self, autoclave_id: int, stats: Dict):
        """Imposta le statistiche di utilizzo per un'autoclave"""
        self.statistiche_autoclavi[autoclave_id] = stats
        
    def imposta_ciclo_cura_autoclave(self, autoclave_id: int, ciclo_info: Dict):
        """Imposta le informazioni del ciclo di cura per un'autoclave"""
        self.cicli_cura_autoclavi[autoclave_id] = ciclo_info

def validate_odl_for_nesting(db: Session, odl: ODL) -> Tuple[bool, str, Dict]:
    """
    Valida se un ODL può essere incluso nel nesting con controlli estesi
    
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
        
        # ✅ NUOVO: Verifica che l'ODL abbia un tool associato
        if not odl.tool:
            return False, "ODL senza tool associato", {}
        
        tool = odl.tool
        
        # Verifica che il catalogo abbia le informazioni necessarie
        if not catalogo.area_cm2 or catalogo.area_cm2 <= 0:
            return False, "Area della parte non definita o non valida", {}
        
        # ✅ NUOVO: Verifica che il tool abbia dimensioni valide
        if not tool.lunghezza_piano or tool.lunghezza_piano <= 0:
            return False, "Lunghezza piano del tool non definita o non valida", {}
        
        if not tool.larghezza_piano or tool.larghezza_piano <= 0:
            return False, "Larghezza piano del tool non definita o non valida", {}
        
        # Verifica che la parte abbia il numero di valvole richieste
        if not parte.num_valvole_richieste or parte.num_valvole_richieste <= 0:
            return False, "Numero di valvole richieste non definito", {}
        
        # ✅ NUOVO: Verifica che la parte abbia un ciclo di cura associato
        if not parte.ciclo_cura_id:
            return False, "Parte senza ciclo di cura associato", {}
        
        # Verifica che l'ODL non sia già in un nesting attivo
        from models.nesting_result import NestingResult
        existing_nesting = db.query(NestingResult).filter(
            NestingResult.odl_ids.contains([odl.id]),
            NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
        ).first()
        
        if existing_nesting:
            return False, f"ODL già incluso nel nesting #{existing_nesting.id}", {}
        
        # ✅ MIGLIORATO: Prepara i dati dell'ODL per l'ottimizzazione con dimensioni reali
        data = {
            "area_cm2": float(catalogo.area_cm2),
            "num_valvole": int(parte.num_valvole_richieste),
            "priorita": int(odl.priorita) if odl.priorita else 1,
            "part_number": catalogo.part_number,
            "descrizione": parte.descrizione_breve or "Sconosciuta",
            "ciclo_cura_id": parte.ciclo_cura_id,
            "ciclo_cura_nome": parte.ciclo_cura.nome if parte.ciclo_cura else "Sconosciuto",
            # ✅ NUOVO: Dimensioni reali del tool in mm
            "tool_lunghezza_mm": float(tool.lunghezza_piano),
            "tool_larghezza_mm": float(tool.larghezza_piano),
            "tool_peso_kg": float(tool.peso) if tool.peso else 0.0,
            "tool_part_number": tool.part_number_tool,
            "tool_descrizione": tool.descrizione or "Sconosciuta"
        }
        
        return True, "", data
        
    except Exception as e:
        logger.error(f"Errore nella validazione ODL {odl.id}: {str(e)}")
        return False, f"Errore nella validazione ODL: {str(e)}", {}

def calculate_2d_positioning(
    odl_data: List[Dict], 
    autoclave_width_mm: float, 
    autoclave_height_mm: float,
    parametri: Optional['NestingParameters'] = None
) -> List[Dict]:
    """
    Calcola il posizionamento 2D reale dei tool sul piano dell'autoclave
    usando un algoritmo di bin packing 2D semplificato
    
    Args:
        odl_data: Lista dei dati degli ODL con dimensioni tool
        autoclave_width_mm: Larghezza del piano autoclave in mm
        autoclave_height_mm: Lunghezza del piano autoclave in mm
        
    Returns:
        Lista di dizionari con posizioni calcolate per ogni ODL
    """
    positioned_tools = []
    
    # Ordina gli ODL per area decrescente (strategia First Fit Decreasing)
    sorted_odl_data = sorted(
        enumerate(odl_data), 
        key=lambda x: x[1]["tool_lunghezza_mm"] * x[1]["tool_larghezza_mm"], 
        reverse=True
    )
    
    # ✅ NUOVO: Usa parametri personalizzati o valori di default
    if parametri:
        # Converti da cm a mm
        margin_mm = parametri.spaziatura_tra_tool_cm * 10.0
        perimeter_margin_mm = parametri.distanza_perimetrale_cm * 10.0
        rotation_enabled = parametri.rotazione_tool_abilitata
    else:
        # Valori di default
        margin_mm = 5.0  # 0.5 cm
        perimeter_margin_mm = 10.0  # 1.0 cm
        rotation_enabled = True
    
    # Lista delle aree occupate: [(x, y, width, height), ...]
    occupied_areas = []
    
    def check_overlap(x, y, width, height, occupied_areas):
        """Verifica se una posizione si sovrappone con aree già occupate"""
        for ox, oy, ow, oh in occupied_areas:
            if not (x >= ox + ow + margin_mm or 
                   x + width + margin_mm <= ox or 
                   y >= oy + oh + margin_mm or 
                   y + height + margin_mm <= oy):
                return True
        return False
    
    def find_position(width, height, autoclave_width, autoclave_height, occupied_areas):
        """Trova la prima posizione disponibile per un tool"""
        # Prova posizioni con step di 10mm per efficienza
        step = 10.0
        
        # ✅ NUOVO: Considera il margine perimetrale
        effective_width = autoclave_width - 2 * perimeter_margin_mm
        effective_height = autoclave_height - 2 * perimeter_margin_mm
        
        for y in range(int(perimeter_margin_mm), int(effective_height - height + perimeter_margin_mm + 1), int(step)):
            for x in range(int(perimeter_margin_mm), int(effective_width - width + perimeter_margin_mm + 1), int(step)):
                if not check_overlap(x, y, width, height, occupied_areas):
                    return x, y
        return None, None
    
    # Posiziona ogni tool
    for original_index, data in sorted_odl_data:
        tool_width = data["tool_lunghezza_mm"]
        tool_height = data["tool_larghezza_mm"]
        
        # ✅ NUOVO: Prova rotazione se abilitata
        positions_to_try = [(tool_width, tool_height, False)]  # (width, height, rotated)
        if rotation_enabled and tool_width != tool_height:
            positions_to_try.append((tool_height, tool_width, True))  # Ruotato di 90°
        
        # ✅ NUOVO: Prova tutte le orientazioni possibili
        positioned = False
        for width, height, rotated in positions_to_try:
            # Verifica se il tool entra fisicamente nell'autoclave
            if width > autoclave_width_mm or height > autoclave_height_mm:
                continue  # Prova la prossima orientazione
            
            # Trova una posizione per il tool
            x, y = find_position(width, height, autoclave_width_mm, autoclave_height_mm, occupied_areas)
            
            if x is not None and y is not None:
                # Posizione trovata
                positioned_tools.append({
                    "original_index": original_index,
                    "positioned": True,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "rotated": rotated
                })
                
                # Aggiungi l'area occupata
                occupied_areas.append((x, y, width, height))
                
                rotation_msg = " (ruotato 90°)" if rotated else ""
                logger.debug(f"Tool ODL {data.get('part_number', 'N/A')} posizionato a ({x:.1f}, {y:.1f}){rotation_msg}")
                positioned = True
                break
        
        if not positioned:
            # Nessuna posizione disponibile in nessuna orientazione
            positioned_tools.append({
                "original_index": original_index,
                "positioned": False,
                "reason": "Nessuna posizione disponibile sul piano (provate tutte le orientazioni)"
            })
            logger.warning(f"Tool ODL {data.get('part_number', 'N/A')} non posizionabile - spazio insufficiente")
    
    return positioned_tools

def group_odl_by_ciclo_cura(odl_validi: List[ODL], odl_data: List[Dict]) -> Dict[int, List[Tuple[ODL, Dict]]]:
    """
    Raggruppa gli ODL per ciclo di cura compatibile
    
    Args:
        odl_validi: Lista degli ODL validati
        odl_data: Lista dei dati corrispondenti agli ODL
        
    Returns:
        Dizionario che mappa ciclo_cura_id -> [(odl, data), ...]
    """
    gruppi_cicli = {}
    
    for odl, data in zip(odl_validi, odl_data):
        ciclo_id = data["ciclo_cura_id"]
        if ciclo_id not in gruppi_cicli:
            gruppi_cicli[ciclo_id] = []
        gruppi_cicli[ciclo_id].append((odl, data))
    
    return gruppi_cicli

def check_autoclave_availability(db: Session, autoclave: Autoclave) -> Tuple[bool, str]:
    """
    Verifica se un'autoclave è disponibile per il nesting
    
    Args:
        db: Sessione del database
        autoclave: Autoclave da verificare
        
    Returns:
        Tupla (is_available, error_message)
    """
    try:
        # Verifica che l'autoclave sia in stato disponibile
        if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
            return False, f"Autoclave non disponibile (stato: {autoclave.stato})"
        
        # Verifica che l'autoclave abbia dimensioni valide
        if not autoclave.lunghezza or autoclave.lunghezza <= 0:
            return False, "Lunghezza autoclave non definita"
        
        if not autoclave.larghezza_piano or autoclave.larghezza_piano <= 0:
            return False, "Larghezza piano autoclave non definita"
        
        # Verifica che l'autoclave abbia linee vuoto disponibili
        if not autoclave.num_linee_vuoto or autoclave.num_linee_vuoto <= 0:
            return False, "Numero linee vuoto non definito"
        
        # Verifica che non ci siano nesting attivi per questa autoclave
        from models.nesting_result import NestingResult
        active_nesting = db.query(NestingResult).filter(
            NestingResult.autoclave_id == autoclave.id,
            NestingResult.stato.in_(["Schedulato", "In corso"])
        ).first()
        
        if active_nesting:
            return False, f"Autoclave già occupata dal nesting #{active_nesting.id}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Errore nella verifica autoclave: {str(e)}"

def compute_nesting(
    db: Session, 
    odl_list: List[ODL], 
    autoclavi: List[Autoclave],
    parametri: Optional['NestingParameters'] = None
) -> NestingResult:
    """
    Calcola il miglior posizionamento degli ODL nelle autoclavi disponibili.
    
    Args:
        db: Sessione del database
        odl_list: Lista degli ODL da pianificare
        autoclavi: Lista delle autoclavi disponibili
        
    Returns:
        Un oggetto NestingResult con i risultati dell'ottimizzazione
    """
    # Inizializza il risultato
    result = NestingResult()
    
    # Se non ci sono ODL o autoclavi, restituisci subito
    if not odl_list or not autoclavi:
        return result
    
    # Filtra solo gli ODL in stato "Attesa Cura"
    odl_validi = []
    odl_data = []
    
    for odl in odl_list:
        if odl.status != "Attesa Cura":
            result.aggiungi_non_pianificabile(
                odl.id, 
                f"ODL non in stato 'Attesa Cura' (stato attuale: {odl.status})"
            )
            continue
            
        is_valid, error_msg, data = validate_odl_for_nesting(db, odl)
        if not is_valid:
            result.aggiungi_non_pianificabile(odl.id, error_msg)
            continue
            
        odl_validi.append(odl)
        odl_data.append(data)
    
    # Filtra autoclavi disponibili
    autoclavi_valide = []
    
    for autoclave in autoclavi:
        is_available, error_msg = check_autoclave_availability(db, autoclave)
        if not is_available:
            # Non aggiungiamo l'autoclave al problema
            continue
        autoclavi_valide.append(autoclave)
    
    # Se non abbiamo ODL o autoclavi valide, restituisci
    if not odl_validi or not autoclavi_valide:
        # Tutti gli ODL rimanenti sono non pianificabili per mancanza di autoclavi
        for odl in odl_validi:
            result.aggiungi_non_pianificabile(odl.id, "Nessuna autoclave disponibile")
        return result
    
    # ✅ NUOVO: Raggruppa gli ODL per ciclo di cura
    gruppi_cicli = group_odl_by_ciclo_cura(odl_validi, odl_data)
    
    # Processa ogni gruppo di ciclo di cura separatamente
    for ciclo_id, gruppo_odl_data in gruppi_cicli.items():
        # Estrai ODL e dati per questo ciclo
        gruppo_odl = [item[0] for item in gruppo_odl_data]
        gruppo_data = [item[1] for item in gruppo_odl_data]
        
        # Ottieni informazioni sul ciclo di cura
        ciclo_info = {
            "id": ciclo_id,
            "nome": gruppo_data[0]["ciclo_cura_nome"] if gruppo_data else "Sconosciuto"
        }
        
        # Esegui l'ottimizzazione per questo gruppo
        gruppo_result = _optimize_single_cycle_group(db, gruppo_odl, gruppo_data, autoclavi_valide, ciclo_info)
        
        # Aggiungi i risultati al risultato principale
        for autoclave_id, odl_ids in gruppo_result.assegnamenti.items():
            for odl_id in odl_ids:
                result.aggiungi_assegnamento(autoclave_id, odl_id)
            
            # Imposta le informazioni del ciclo di cura per l'autoclave
            result.imposta_ciclo_cura_autoclave(autoclave_id, ciclo_info)
        
        # Aggiungi statistiche autoclavi
        for autoclave_id, stats in gruppo_result.statistiche_autoclavi.items():
            result.imposta_statistiche_autoclave(autoclave_id, stats)
        
        # Aggiungi ODL non pianificabili
        for item in gruppo_result.odl_non_pianificabili:
            result.aggiungi_non_pianificabile(item["odl_id"], item["motivo"])
    
    return result

def _optimize_single_cycle_group(
    db: Session, 
    odl_list: List[ODL], 
    odl_data: List[Dict], 
    autoclavi: List[Autoclave],
    ciclo_info: Dict
) -> NestingResult:
    """
    Ottimizza un singolo gruppo di ODL con lo stesso ciclo di cura
    usando posizionamento 2D reale e vincoli fisici migliorati
    
    Args:
        db: Sessione del database
        odl_list: Lista degli ODL con lo stesso ciclo di cura
        odl_data: Dati corrispondenti agli ODL
        autoclavi: Lista delle autoclavi disponibili
        ciclo_info: Informazioni sul ciclo di cura
        
    Returns:
        Un oggetto NestingResult con i risultati dell'ottimizzazione per questo gruppo
    """
    # Inizializza il risultato per questo gruppo
    result = NestingResult()
    
    # Se non ci sono ODL, restituisci subito
    if not odl_list:
        return result
    
    logger.info(f"🔧 Ottimizzazione gruppo ciclo {ciclo_info.get('nome', 'Sconosciuto')} con {len(odl_list)} ODL")
    
    # ✅ NUOVO APPROCCIO: Prova il posizionamento 2D reale per ogni autoclave
    for autoclave in autoclavi:
        logger.info(f"🏭 Tentativo posizionamento su autoclave {autoclave.nome}")
        
        # Calcola il posizionamento 2D per questa autoclave
        positioned_tools = calculate_2d_positioning(
            odl_data, 
            autoclave.larghezza_piano,  # Larghezza del piano
            autoclave.lunghezza         # Lunghezza del piano
        )
        
        # Separa ODL posizionabili da quelli non posizionabili
        posizionabili = []
        non_posizionabili = []
        
        for pos_info in positioned_tools:
            original_index = pos_info["original_index"]
            if pos_info["positioned"]:
                posizionabili.append({
                    "odl": odl_list[original_index],
                    "data": odl_data[original_index],
                    "position": {
                        "x": pos_info["x"],
                        "y": pos_info["y"],
                        "width": pos_info["width"],
                        "height": pos_info["height"]
                    }
                })
            else:
                non_posizionabili.append({
                    "odl": odl_list[original_index],
                    "reason": pos_info.get("reason", "Posizionamento fallito")
                })
        
        # Verifica vincoli aggiuntivi per gli ODL posizionabili
        odl_finali = []
        valvole_totali = 0
        area_utilizzata_cm2 = 0.0
        
        # ✅ NUOVO: Ordina per peso decrescente (parti pesanti nel piano inferiore)
        posizionabili_ordinati = sorted(
            posizionabili, 
            key=lambda x: x["data"].get("tool_peso_kg", 0), 
            reverse=True
        )
        
        for item in posizionabili_ordinati:
            odl = item["odl"]
            data = item["data"]
            position = item["position"]
            
            # Verifica vincolo valvole
            if valvole_totali + data["num_valvole"] <= autoclave.num_linee_vuoto:
                # Verifica vincolo area (controllo aggiuntivo)
                area_tool_cm2 = (data["tool_lunghezza_mm"] * data["tool_larghezza_mm"]) / 100
                area_totale_autoclave_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
                
                if area_utilizzata_cm2 + area_tool_cm2 <= area_totale_autoclave_cm2:
                    # Vincolo altezza rimosso - non disponibile nel modello Tool
                    
                    # ODL accettato
                    odl_finali.append(item)
                    valvole_totali += data["num_valvole"]
                    area_utilizzata_cm2 += area_tool_cm2
                    
                    # Aggiungi assegnamento con posizione
                    result.aggiungi_assegnamento(autoclave.id, odl.id, position)
                    
                    logger.debug(f"✅ ODL {odl.id} assegnato a posizione ({position['x']:.1f}, {position['y']:.1f})")
                else:
                    non_posizionabili.append({
                        "odl": odl,
                        "reason": "Area totale superata"
                    })
            else:
                non_posizionabili.append({
                    "odl": odl,
                    "reason": "Numero valvole superato"
                })
        
        # Se abbiamo posizionato almeno un ODL, salva le statistiche
        if odl_finali:
            area_totale_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
            
            result.imposta_statistiche_autoclave(
                autoclave.id, 
                {
                    "area_totale": area_totale_cm2,
                    "area_utilizzata": area_utilizzata_cm2,
                    "valvole_totali": autoclave.num_linee_vuoto,
                    "valvole_utilizzate": valvole_totali,
                    "odl_posizionati": len(odl_finali),
                    "efficienza_area": (area_utilizzata_cm2 / area_totale_cm2) * 100 if area_totale_cm2 > 0 else 0,
                    "efficienza_valvole": (valvole_totali / autoclave.num_linee_vuoto) * 100 if autoclave.num_linee_vuoto > 0 else 0
                }
            )
            
            logger.info(f"✅ Autoclave {autoclave.nome}: {len(odl_finali)} ODL posizionati, "
                       f"efficienza area: {(area_utilizzata_cm2 / area_totale_cm2) * 100:.1f}%, "
                       f"efficienza valvole: {(valvole_totali / autoclave.num_linee_vuoto) * 100:.1f}%")
            
            # Se abbiamo una buona efficienza, fermiamoci qui
            # (strategia greedy: prima autoclave che funziona bene)
            if len(odl_finali) >= len(odl_list) * 0.8:  # 80% degli ODL posizionati
                logger.info(f"🎯 Efficienza alta raggiunta, utilizzo autoclave {autoclave.nome}")
                break
    
    # Aggiungi tutti gli ODL non assegnati come non pianificabili
    odl_assegnati = set()
    for autoclave_id, odl_ids in result.assegnamenti.items():
        odl_assegnati.update(odl_ids)
    
    for odl in odl_list:
        if odl.id not in odl_assegnati:
            result.aggiungi_non_pianificabile(odl.id, "Nessuna autoclave con spazio sufficiente per posizionamento 2D")
    
    return result 