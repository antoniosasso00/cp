"""
Modulo principale per l'ottimizzazione del nesting con OR-Tools.
"""

import time
import random
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from ortools.linear_solver import pywraplp

from models import Autoclave, ODL, Tool, Parte, NestingParams, NestingResult
from .schemas import (
    NestingParameters, NestingRequest, NestingResponse, 
    AutoclaveLayout, ODLLayout
)

logger = logging.getLogger(__name__)

class NestingOptimizer:
    """
    Classe principale per l'ottimizzazione del nesting usando OR-Tools.
    Implementa algoritmi di ottimizzazione per posizionare gli ODL nelle autoclavi.
    """
    
    def __init__(self, db: Session):
        """
        Inizializza l'ottimizzatore con una sessione di database.
        
        Args:
            db: Sessione di database SQLAlchemy
        """
        self.db = db
        self.default_parameters = NestingParameters()
    
    def get_active_parameters(self) -> NestingParameters:
        """
        Ottiene i parametri attivi dal database o restituisce i parametri di default.
        
        Returns:
            NestingParameters: Parametri attivi per l'ottimizzazione
        """
        active_params = self.db.query(NestingParams).filter(NestingParams.attivo == True).first()
        
        if active_params:
            return NestingParameters(
                peso_valvole=active_params.peso_valvole,
                peso_area=active_params.peso_area,
                peso_priorita=active_params.peso_priorita,
                spazio_minimo_mm=active_params.spazio_minimo_mm
            )
        
        return self.default_parameters
    
    def update_parameters(self, params: NestingParameters) -> bool:
        """
        Aggiorna i parametri attivi nel database.
        
        Args:
            params: Nuovi parametri da salvare
            
        Returns:
            bool: True se l'aggiornamento è avvenuto con successo
        """
        # Imposta tutti i parametri esistenti come non attivi
        self.db.query(NestingParams).filter(NestingParams.attivo == True).update({"attivo": False})
        
        # Crea nuovi parametri attivi
        new_params = NestingParams(
            nome=f"Configurazione_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            peso_valvole=params.peso_valvole,
            peso_area=params.peso_area,
            peso_priorita=params.peso_priorita,
            spazio_minimo_mm=params.spazio_minimo_mm,
            attivo=True,
            descrizione="Configurazione generata automaticamente"
        )
        
        self.db.add(new_params)
        self.db.commit()
        return True
    
    def get_available_odls(self, odl_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Ottiene la lista di ODL disponibili per il nesting.
        
        Args:
            odl_ids: Lista opzionale di ID degli ODL da considerare
            
        Returns:
            List[Dict]: Informazioni sugli ODL disponibili
        """
        query = self.db.query(
            ODL, Tool, Parte
        ).join(
            Tool, ODL.tool_id == Tool.id
        ).join(
            Parte, ODL.parte_id == Parte.id
        ).filter(
            ODL.status == "Attesa Cura"
        )
        
        if odl_ids:
            query = query.filter(ODL.id.in_(odl_ids))
        
        results = []
        for odl, tool, parte in query.all():
            results.append({
                "odl_id": odl.id,
                "priorita": odl.priorita,
                "parte_id": parte.id,
                "parte_nome": parte.descrizione_breve,
                "tool_id": tool.id,
                "tool_codice": tool.codice,
                "lunghezza": tool.lunghezza_piano,
                "larghezza": tool.larghezza_piano,
                "area": tool.lunghezza_piano * tool.larghezza_piano,
                "valvole_richieste": parte.num_valvole_richieste,
                "ciclo_cura_id": parte.ciclo_cura_id
            })
        
        return results
    
    def get_available_autoclaves(self, autoclave_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Ottiene la lista di autoclavi disponibili per il nesting.
        
        Args:
            autoclave_ids: Lista opzionale di ID delle autoclavi da considerare
            
        Returns:
            List[Dict]: Informazioni sulle autoclavi disponibili
        """
        query = self.db.query(Autoclave).filter(Autoclave.stato == "DISPONIBILE")
        
        if autoclave_ids:
            query = query.filter(Autoclave.id.in_(autoclave_ids))
        
        results = []
        for autoclave in query.all():
            results.append({
                "id": autoclave.id,
                "nome": autoclave.nome,
                "lunghezza": autoclave.lunghezza,
                "larghezza": autoclave.larghezza_piano,
                "area": autoclave.lunghezza * autoclave.larghezza_piano,
                "num_linee_vuoto": autoclave.num_linee_vuoto
            })
        
        return results
    
    def optimize_nesting(self, request: NestingRequest) -> NestingResponse:
        """
        Ottimizza il nesting degli ODL nelle autoclavi disponibili.
        
        Args:
            request: Richiesta di nesting con parametri e ODL da posizionare
            
        Returns:
            NestingResponse: Risultato dell'ottimizzazione con layout per ogni autoclave
        """
        start_time = time.time()
        
        # Ottieni le autoclavi disponibili
        autoclaves = self.get_available_autoclaves(request.autoclave_ids)
        if not autoclaves:
            return NestingResponse(
                success=False,
                message="Nessuna autoclave disponibile per il nesting."
            )
        
        # Ottieni gli ODL da posizionare
        odls = self.get_available_odls(request.odl_ids)
        if not odls:
            return NestingResponse(
                success=False,
                message="Nessun ODL valido da posizionare."
            )
        
        # Raggruppa gli ODL per ciclo
        ciclo_groups = self._group_odls_by_ciclo(odls)
        
        # Per il nesting manuale, usa solo gli ODL specificati
        if request.manual and request.odl_ids:
            manual_odls = [odl for odl in odls if odl["odl_id"] in request.odl_ids]
            result = self._pack_single_autoclave(manual_odls, autoclaves[0], request.params)
            
            layout = AutoclaveLayout(
                autoclave_id=autoclaves[0]["id"],
                autoclave_nome=autoclaves[0]["nome"],
                odl_layout=result["odl_layout"],
                area_totale_mm2=result["area_totale_mm2"],
                area_utilizzata_mm2=result["area_utilizzata_mm2"],
                efficienza_area=result["efficienza_area"],
                valvole_totali=result["valvole_totali"],
                valvole_utilizzate=result["valvole_utilizzate"],
                nesting_id=result.get("nesting_id")
            )
            
            return NestingResponse(
                success=True,
                message="Nesting manuale completato.",
                layouts=[layout]
            )
        
        # Per il nesting automatico
        final_layouts = []
        remaining_odls = [odl for group in ciclo_groups for odl in group]
        
        # Prova a posizionare gli ODL in ogni autoclave
        for autoclave in autoclaves:
            # Se non ci sono più ODL da posizionare, esci
            if not remaining_odls:
                break
            
            # Seleziona gli ODL da posizionare in questa autoclave
            odls_for_autoclave = self._select_odls_for_autoclave(
                remaining_odls,
                autoclave,
                request.params
            )
            
            # Se abbiamo ODL da posizionare nell'autoclave corrente
            if odls_for_autoclave:
                # Ottimizza il layout per questa autoclave
                result = self._pack_single_autoclave(odls_for_autoclave, autoclave, request.params)
                
                # Crea il layout
                layout = AutoclaveLayout(
                    autoclave_id=autoclave["id"],
                    autoclave_nome=autoclave["nome"],
                    odl_layout=result["odl_layout"],
                    area_totale_mm2=result["area_totale_mm2"],
                    area_utilizzata_mm2=result["area_utilizzata_mm2"],
                    efficienza_area=result["efficienza_area"],
                    valvole_totali=result["valvole_totali"],
                    valvole_utilizzate=result["valvole_utilizzate"],
                    nesting_id=result.get("nesting_id")
                )
                
                final_layouts.append(layout)
                
                # Rimuovi gli ODL assegnati da quelli rimanenti
                packed_odl_ids = [odl["odl_id"] for odl in odls_for_autoclave]
                remaining_odls = [odl for odl in remaining_odls if odl["odl_id"] not in packed_odl_ids]
                
                # Aggiorna i gruppi
                for group in ciclo_groups:
                    group[:] = [odl for odl in group if odl["odl_id"] not in packed_odl_ids]
        
        processing_time = time.time() - start_time
        
        if not final_layouts:
            return NestingResponse(
                success=False,
                message="Impossibile trovare una soluzione di nesting valida."
            )
        
        return NestingResponse(
            success=True,
            message=f"Nesting ottimizzato completato in {processing_time:.2f} secondi.",
            layouts=final_layouts
        )
    
    def save_nesting_result(self, layout: AutoclaveLayout, manual: bool = False) -> int:
        """
        Salva il risultato del nesting nel database.
        
        Args:
            layout: Layout dell'autoclave con gli ODL posizionati
            manual: Flag che indica se il nesting è stato generato manualmente
            
        Returns:
            int: ID del risultato di nesting salvato
        """
        # Genera un codice univoco per il risultato
        codice = f"NEST-{uuid.uuid4().hex[:8].upper()}"
        
        # Crea un nuovo risultato
        nesting_result = NestingResult(
            codice=codice,
            autoclave_id=layout.autoclave_id,
            confermato=False,
            area_totale_mm2=layout.area_totale_mm2,
            area_utilizzata_mm2=layout.area_utilizzata_mm2,
            efficienza_area=layout.efficienza_area,
            valvole_totali=layout.valvole_totali,
            valvole_utilizzate=layout.valvole_utilizzate,
            layout=[odl.dict() for odl in layout.odl_layout],
            odl_ids=[odl.odl_id for odl in layout.odl_layout],
            generato_manualmente=manual
        )
        
        self.db.add(nesting_result)
        self.db.commit()
        self.db.refresh(nesting_result)
        
        return nesting_result.id
    
    def confirm_nesting(self, nesting_id: int) -> bool:
        """
        Conferma un risultato di nesting e aggiorna lo stato degli ODL.
        
        Args:
            nesting_id: ID del risultato di nesting da confermare
            
        Returns:
            bool: True se la conferma è avvenuta con successo
        """
        nesting_result = self.db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        
        if not nesting_result:
            return False
            
        if nesting_result.confermato:
            return True  # Già confermato
        
        # Aggiorna il risultato
        nesting_result.confermato = True
        nesting_result.data_conferma = datetime.now()
        
        # Aggiorna lo stato degli ODL a "Cura"
        odl_ids = nesting_result.odl_ids
        self.db.query(ODL).filter(ODL.id.in_(odl_ids)).update({"status": "Cura"}, synchronize_session=False)
        
        # Aggiorna lo stato dell'autoclave a "IN_USO"
        self.db.query(Autoclave).filter(
            Autoclave.id == nesting_result.autoclave_id
        ).update({"stato": "IN_USO"}, synchronize_session=False)
        
        self.db.commit()
        return True
    
    def _pack_single_autoclave(
        self, 
        odls: List[Dict[str, Any]], 
        autoclave: Dict[str, Any],
        params: NestingParameters,
        nesting_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Implementa l'algoritmo di bin packing 2D per una singola autoclave.
        Utilizza OR-Tools per ottimizzare il posizionamento.
        
        Args:
            odls: Lista di ODL da posizionare
            autoclave: Informazioni sull'autoclave
            params: Parametri di ottimizzazione
            nesting_id: ID opzionale del risultato di nesting
            
        Returns:
            Dict: Risultato dell'ottimizzazione con layout degli ODL
        """
        # Dimensioni dell'autoclave
        width = autoclave["larghezza"]
        length = autoclave["lunghezza"]
        total_area = width * length
        
        # Crea il solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        
        if not solver:
            raise Exception("Impossibile creare il solver OR-Tools")
        
        # Variabili: posizione (x, y) per ogni ODL
        x = {}
        y = {}
        for i, odl in enumerate(odls):
            x[i] = solver.NumVar(0, length - odl["lunghezza"], f'x_{i}')
            y[i] = solver.NumVar(0, width - odl["larghezza"], f'y_{i}')
        
        # Variabili binarie per determinare la relativa posizione degli ODL
        # 1 se l'ODL i è a destra dell'ODL j, 0 altrimenti
        right = {}
        # 1 se l'ODL i è sopra l'ODL j, 0 altrimenti
        above = {}
        
        # Aggiungi i vincoli di non sovrapposizione
        M = max(length, width) * 2  # Un valore grande per i vincoli big-M
        for i in range(len(odls)):
            for j in range(i + 1, len(odls)):
                right[(i, j)] = solver.BoolVar(f'right_{i}_{j}')
                right[(j, i)] = solver.BoolVar(f'right_{j}_{i}')
                above[(i, j)] = solver.BoolVar(f'above_{i}_{j}')
                above[(j, i)] = solver.BoolVar(f'above_{j}_{i}')
                
                # ODL i a destra di j o viceversa
                solver.Add(x[i] >= x[j] + odls[j]["lunghezza"] + params.spazio_minimo_mm - M * (1 - right[(i, j)]))
                solver.Add(x[j] >= x[i] + odls[i]["lunghezza"] + params.spazio_minimo_mm - M * (1 - right[(j, i)]))
                
                # ODL i sopra a j o viceversa
                solver.Add(y[i] >= y[j] + odls[j]["larghezza"] + params.spazio_minimo_mm - M * (1 - above[(i, j)]))
                solver.Add(y[j] >= y[i] + odls[i]["larghezza"] + params.spazio_minimo_mm - M * (1 - above[(j, i)]))
                
                # Almeno una relazione deve essere vera
                solver.Add(right[(i, j)] + right[(j, i)] + above[(i, j)] + above[(j, i)] >= 1)
        
        # Funzione obiettivo: massimizza l'utilizzo dell'area e il numero di ODL con priorità alta
        objective = solver.Objective()
        
        # Componente area (minimizza lo spazio non utilizzato)
        area_weight = params.peso_area
        total_odl_area = sum(odl["area"] for odl in odls)
        
        # Componente priorità (massimizza la somma delle priorità)
        priority_weight = params.peso_priorita
        for i, odl in enumerate(odls):
            objective.SetCoefficient(x[i], 0)  # Solo per includere x nella funzione obiettivo
            objective.SetCoefficient(y[i], 0)  # Solo per includere y nella funzione obiettivo
            objective.SetCoefficient(right.get((i, 0), right.get((0, i), solver.BoolVar('dummy'))), 0)  # Solo una dummy
            
            # Aggiungi un bonus per priorità alta
            # Questo è un trucco poiché OR-Tools non supporta direttamente l'ottimizzazione multi-obiettivo
            priority_bonus = odl["priorita"] * priority_weight / 10.0
            objective.SetCoefficient(x[i], priority_bonus)
        
        # Massimizza l'efficienza dell'area
        area_efficiency = total_odl_area / total_area * area_weight
        objective.SetCoefficient(x[0], area_efficiency)  # Aggiungiamo all'ODL 0 come proxy
        
        objective.SetMaximization()
        
        # Risolvi il problema
        status = solver.Solve()
        
        if status != pywraplp.Solver.OPTIMAL and status != pywraplp.Solver.FEASIBLE:
            # Fallback: usa un algoritmo greedy semplice se l'ottimizzazione fallisce
            return self._fallback_greedy_packing(odls, autoclave, params)
        
        # Costruisci il layout risultante
        odl_layout = []
        area_used = 0
        valves_used = 0
        
        for i, odl in enumerate(odls):
            pos_x = x[i].solution_value()
            pos_y = y[i].solution_value()
            
            odl_layout.append(ODLLayout(
                odl_id=odl["odl_id"],
                x=pos_x,
                y=pos_y,
                lunghezza=odl["lunghezza"],
                larghezza=odl["larghezza"],
                valvole_utilizzate=odl["valvole_richieste"],
                parte_nome=odl["parte_nome"],
                tool_codice=odl["tool_codice"],
                priorita=odl["priorita"]
            ))
            
            area_used += odl["area"]
            valves_used += odl["valvole_richieste"]
        
        return {
            "odl_layout": odl_layout,
            "area_totale_mm2": total_area,
            "area_utilizzata_mm2": area_used,
            "efficienza_area": area_used / total_area if total_area > 0 else 0,
            "valvole_totali": autoclave["num_linee_vuoto"],
            "valvole_utilizzate": valves_used,
            "nesting_id": nesting_id
        }
    
    def _fallback_greedy_packing(
        self, 
        odls: List[Dict[str, Any]], 
        autoclave: Dict[str, Any],
        params: NestingParameters
    ) -> Dict[str, Any]:
        """
        Algoritmo fallback greedy per il posizionamento quando OR-Tools fallisce.
        
        Args:
            odls: Lista di ODL da posizionare
            autoclave: Informazioni sull'autoclave
            params: Parametri di ottimizzazione
            
        Returns:
            Dict: Risultato dell'ottimizzazione con layout degli ODL
        """
        # Ordina gli ODL per area decrescente
        sorted_odls = sorted(odls, key=lambda x: x["area"], reverse=True)
        
        # Dimensioni dell'autoclave
        width = autoclave["larghezza"]
        length = autoclave["lunghezza"]
        total_area = width * length
        
        # Posiziona gli ODL in una griglia
        odl_layout = []
        area_used = 0
        valves_used = 0
        
        current_x = 0
        current_y = 0
        row_height = 0
        
        for odl in sorted_odls:
            # Se l'ODL non entra nella riga corrente, vai alla riga successiva
            if current_x + odl["lunghezza"] > length:
                current_x = 0
                current_y += row_height + params.spazio_minimo_mm
                row_height = 0
            
            # Se l'ODL non entra nell'autoclave, salta
            if current_y + odl["larghezza"] > width:
                continue
            
            # Posiziona l'ODL
            odl_layout.append(ODLLayout(
                odl_id=odl["odl_id"],
                x=current_x,
                y=current_y,
                lunghezza=odl["lunghezza"],
                larghezza=odl["larghezza"],
                valvole_utilizzate=odl["valvole_richieste"],
                parte_nome=odl["parte_nome"],
                tool_codice=odl["tool_codice"],
                priorita=odl["priorita"]
            ))
            
            area_used += odl["area"]
            valves_used += odl["valvole_richieste"]
            
            # Aggiorna la posizione e l'altezza della riga
            current_x += odl["lunghezza"] + params.spazio_minimo_mm
            row_height = max(row_height, odl["larghezza"])
            
            # Controlla se abbiamo superato il limite di valvole
            if valves_used > autoclave["num_linee_vuoto"]:
                # Rimuovi l'ultimo ODL aggiunto
                last_odl = odl_layout.pop()
                area_used -= odl["area"]
                valves_used -= odl["valvole_richieste"]
                break
        
        return {
            "odl_layout": odl_layout,
            "area_totale_mm2": total_area,
            "area_utilizzata_mm2": area_used,
            "efficienza_area": area_used / total_area if total_area > 0 else 0,
            "valvole_totali": autoclave["num_linee_vuoto"],
            "valvole_utilizzate": valves_used
        } 