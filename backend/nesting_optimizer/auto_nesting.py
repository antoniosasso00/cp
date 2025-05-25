"""
Modulo per l'ottimizzazione del nesting automatico degli ODL nelle autoclavi
utilizzando Google OR-Tools.
"""

from typing import List, Dict, Tuple, Optional
from ortools.linear_solver import pywraplp
from sqlalchemy.orm import Session, joinedload
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte
from models.catalogo import Catalogo

class NestingResult:
    """Classe per contenere il risultato dell'ottimizzazione di nesting"""
    
    def __init__(self):
        # Mappatura autoclave_id -> [odl_ids]
        self.assegnamenti: Dict[int, List[int]] = {}
        # Lista di ODL non assegnabili con motivazioni
        self.odl_non_pianificabili: List[Dict] = []
        # Statistiche sull'utilizzo delle autoclavi
        self.statistiche_autoclavi: Dict[int, Dict] = {}
        
    def aggiungi_assegnamento(self, autoclave_id: int, odl_id: int):
        """Aggiunge un assegnamento di un ODL a un'autoclave"""
        if autoclave_id not in self.assegnamenti:
            self.assegnamenti[autoclave_id] = []
        self.assegnamenti[autoclave_id].append(odl_id)
    
    def aggiungi_non_pianificabile(self, odl_id: int, motivo: str):
        """Aggiunge un ODL alla lista di quelli non pianificabili con motivazione"""
        self.odl_non_pianificabili.append({
            "odl_id": odl_id,
            "motivo": motivo
        })
        
    def imposta_statistiche_autoclave(self, autoclave_id: int, stats: Dict):
        """Imposta le statistiche di utilizzo per un'autoclave"""
        self.statistiche_autoclavi[autoclave_id] = stats

def validate_odl_for_nesting(db: Session, odl: ODL) -> Tuple[bool, str, Dict]:
    """
    Valida se un ODL può essere incluso nel nesting
    
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
        
        # Verifica che il catalogo abbia le informazioni necessarie
        if not catalogo.area_cm2 or catalogo.area_cm2 <= 0:
            return False, "Area della parte non definita o non valida", {}
        
        # Verifica che la parte abbia il numero di valvole richieste
        if not parte.num_valvole_richieste or parte.num_valvole_richieste <= 0:
            return False, "Numero di valvole richieste non definito", {}
        
        # Verifica che l'ODL non sia già in un nesting attivo
        from models.nesting_result import NestingResult
        existing_nesting = db.query(NestingResult).filter(
            NestingResult.odl_ids.contains([odl.id]),
            NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
        ).first()
        
        if existing_nesting:
            return False, f"ODL già incluso nel nesting #{existing_nesting.id}", {}
        
        # Prepara i dati dell'ODL per l'ottimizzazione
        data = {
            "area_cm2": float(catalogo.area_cm2),
            "num_valvole": int(parte.num_valvole_richieste),
            "priorita": int(odl.priorita) if odl.priorita else 1,
            "part_number": catalogo.part_number,
            "descrizione": parte.descrizione_breve or "Sconosciuta"
        }
        
        return True, "", data
        
    except Exception as e:
        return False, f"Errore nella validazione ODL: {str(e)}", {}

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
    autoclavi: List[Autoclave]
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
    
    # Crea un solver per un problema di programmazione lineare intera
    solver = pywraplp.Solver.CreateSolver('SCIP')
    
    if not solver:
        # Fallback: assegna in ordine di priorità
        for odl, data in zip(odl_validi, odl_data):
            result.aggiungi_non_pianificabile(odl.id, "Solver non disponibile")
        return result
    
    # Dizionario per tenere traccia delle variabili di decisione
    # x[i][j] = 1 se l'ODL i è assegnato all'autoclave j, 0 altrimenti
    x = {}
    
    # Crea le variabili di decisione
    for i, odl in enumerate(odl_validi):
        x[i] = {}
        for j, autoclave in enumerate(autoclavi_valide):
            x[i][j] = solver.IntVar(0, 1, f'x_{i}_{j}')
    
    # Vincolo 1: ogni ODL può essere assegnato al massimo a un'autoclave
    for i in range(len(odl_validi)):
        solver.Add(solver.Sum([x[i][j] for j in range(len(autoclavi_valide))]) <= 1)
    
    # Vincolo 2: limite di area per ogni autoclave (convertita in cm²)
    for j, autoclave in enumerate(autoclavi_valide):
        area_totale_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100  # mm² -> cm²
        constraint_area = solver.Sum([x[i][j] * odl_data[i]["area_cm2"] for i in range(len(odl_validi))])
        solver.Add(constraint_area <= area_totale_cm2)
    
    # Vincolo 3: limite di valvole per ogni autoclave
    for j, autoclave in enumerate(autoclavi_valide):
        constraint_valvole = solver.Sum([x[i][j] * odl_data[i]["num_valvole"] for i in range(len(odl_validi))])
        solver.Add(constraint_valvole <= autoclave.num_linee_vuoto)
    
    # Funzione obiettivo: massimizzare il numero di ODL assegnati, pesati per priorità
    objective = solver.Sum([
        x[i][j] * odl_data[i]["priorita"] 
        for i in range(len(odl_validi)) 
        for j in range(len(autoclavi_valide))
    ])
    solver.Maximize(objective)
    
    # Risolvi il problema
    status = solver.Solve()
    
    # Processa i risultati
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        # Itera sugli ODL
        for i, odl in enumerate(odl_validi):
            # Controlla se l'ODL è stato assegnato a qualche autoclave
            assigned = False
            for j, autoclave in enumerate(autoclavi_valide):
                if x[i][j].solution_value() > 0.5:  # Se x[i][j] è approssimativamente 1
                    # L'ODL i è assegnato all'autoclave j
                    result.aggiungi_assegnamento(autoclave.id, odl.id)
                    assigned = True
                    break
            
            if not assigned:
                # L'ODL non è stato assegnato a nessuna autoclave
                result.aggiungi_non_pianificabile(odl.id, "Nessuna autoclave con spazio sufficiente")
        
        # Calcola le statistiche per ogni autoclave utilizzata
        for j, autoclave in enumerate(autoclavi_valide):
            area_totale_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
            area_utilizzata_cm2 = sum(x[i][j].solution_value() * odl_data[i]["area_cm2"] for i in range(len(odl_validi)))
            valvole_utilizzate = sum(x[i][j].solution_value() * odl_data[i]["num_valvole"] for i in range(len(odl_validi)))
            
            # Solo se l'autoclave è stata effettivamente utilizzata
            if any(x[i][j].solution_value() > 0.5 for i in range(len(odl_validi))):
                result.imposta_statistiche_autoclave(
                    autoclave.id, 
                    {
                        "area_totale": area_totale_cm2,
                        "area_utilizzata": area_utilizzata_cm2,
                        "valvole_totali": autoclave.num_linee_vuoto,
                        "valvole_utilizzate": int(valvole_utilizzate)
                    }
                )
    else:
        # Nessuna soluzione trovata, tutti gli ODL sono non pianificabili
        for odl in odl_validi:
            result.aggiungi_non_pianificabile(odl.id, "Nessuna soluzione trovata dal solver")
    
    return result 