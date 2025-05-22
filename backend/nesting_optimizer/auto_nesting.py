"""
Modulo per l'ottimizzazione del nesting automatico degli ODL nelle autoclavi
utilizzando Google OR-Tools.
"""

from typing import List, Dict, Tuple, Optional
from ortools.linear_solver import pywraplp
from sqlalchemy.orm import Session
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte

class NestingResult:
    """Classe per contenere il risultato dell'ottimizzazione di nesting"""
    
    def __init__(self):
        # Mappatura autoclave_id -> [odl_ids]
        self.assegnamenti: Dict[int, List[int]] = {}
        # Lista di ODL non assegnabili
        self.odl_non_pianificabili: List[int] = []
        # Statistiche sull'utilizzo delle autoclavi
        self.statistiche_autoclavi: Dict[int, Dict] = {}
        
    def aggiungi_assegnamento(self, autoclave_id: int, odl_id: int):
        """Aggiunge un assegnamento di un ODL a un'autoclave"""
        if autoclave_id not in self.assegnamenti:
            self.assegnamenti[autoclave_id] = []
        self.assegnamenti[autoclave_id].append(odl_id)
    
    def aggiungi_non_pianificabile(self, odl_id: int):
        """Aggiunge un ODL alla lista di quelli non pianificabili"""
        self.odl_non_pianificabili.append(odl_id)
        
    def imposta_statistiche_autoclave(self, autoclave_id: int, stats: Dict):
        """Imposta le statistiche di utilizzo per un'autoclave"""
        self.statistiche_autoclavi[autoclave_id] = stats

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
    
    # Crea un solver per un problema di programmazione lineare intera
    solver = pywraplp.Solver.CreateSolver('SCIP')
    
    if not solver:
        raise RuntimeError("Impossibile creare il solver OR-Tools")
    
    # Dizionario per tenere traccia delle variabili di decisione
    # x[i][j] = 1 se l'ODL i è assegnato all'autoclave j, 0 altrimenti
    x = {}
    
    # Crea le variabili di decisione
    for i, odl in enumerate(odl_list):
        x[i] = {}
        for j, autoclave in enumerate(autoclavi):
            x[i][j] = solver.IntVar(0, 1, f'x_{i}_{j}')
    
    # Vincolo 1: ogni ODL può essere assegnato al massimo a un'autoclave
    for i in range(len(odl_list)):
        solver.Add(solver.Sum([x[i][j] for j in range(len(autoclavi))]) <= 1)
    
    # Calcola area e valvole richieste per ogni ODL
    odl_areas = []
    odl_valvole = []
    
    for odl in odl_list:
        # Recupera la parte associata all'ODL
        parte = db.query(Parte).filter(Parte.id == odl.parte_id).first()
        if not parte:
            # Se la parte non è trovata, considera l'ODL non pianificabile
            result.aggiungi_non_pianificabile(odl.id)
            continue
        
        # Calcola l'area dell'ODL (qui usiamo un valore fisso per semplicità)
        # In un'implementazione reale, questo dovrebbe essere calcolato in base alla geometria della parte
        area_odl = 1.0  # Valore fittizio di default
        
        odl_areas.append(area_odl)
        odl_valvole.append(parte.num_valvole_richieste)
    
    # Vincolo 2: limite di area per ogni autoclave
    for j, autoclave in enumerate(autoclavi):
        area_totale = autoclave.lunghezza * autoclave.larghezza_piano
        constraint_area = solver.Sum([x[i][j] * odl_areas[i] for i in range(len(odl_list))])
        solver.Add(constraint_area <= area_totale)
    
    # Vincolo 3: limite di valvole per ogni autoclave
    for j, autoclave in enumerate(autoclavi):
        constraint_valvole = solver.Sum([x[i][j] * odl_valvole[i] for i in range(len(odl_list))])
        solver.Add(constraint_valvole <= autoclave.num_linee_vuoto)
    
    # Funzione obiettivo: massimizzare il numero di ODL assegnati, pesati per priorità
    objective = solver.Sum([x[i][j] * odl_list[i].priorita for i in range(len(odl_list)) for j in range(len(autoclavi))])
    solver.Maximize(objective)
    
    # Risolvi il problema
    status = solver.Solve()
    
    # Processa i risultati
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        # Itera sugli ODL
        for i, odl in enumerate(odl_list):
            # Controlla se l'ODL è stato assegnato a qualche autoclave
            assigned = False
            for j, autoclave in enumerate(autoclavi):
                if x[i][j].solution_value() > 0.5:  # Se x[i][j] è approssimativamente 1
                    # L'ODL i è assegnato all'autoclave j
                    result.aggiungi_assegnamento(autoclave.id, odl.id)
                    assigned = True
                    break
            
            if not assigned:
                # L'ODL non è stato assegnato a nessuna autoclave
                result.aggiungi_non_pianificabile(odl.id)
        
        # Calcola le statistiche per ogni autoclave
        for j, autoclave in enumerate(autoclavi):
            area_totale = autoclave.lunghezza * autoclave.larghezza_piano
            area_utilizzata = sum(x[i][j].solution_value() * odl_areas[i] for i in range(len(odl_list)))
            valvole_utilizzate = sum(x[i][j].solution_value() * odl_valvole[i] for i in range(len(odl_list)))
            
            result.imposta_statistiche_autoclave(
                autoclave.id, 
                {
                    "area_totale": area_totale,
                    "area_utilizzata": area_utilizzata,
                    "valvole_totali": autoclave.num_linee_vuoto,
                    "valvole_utilizzate": valvole_utilizzate
                }
            )
    else:
        # Nessuna soluzione trovata, tutti gli ODL sono non pianificabili
        for odl in odl_list:
            result.aggiungi_non_pianificabile(odl.id)
    
    return result 