"""
Modulo per l'ottimizzazione automatica del nesting degli ODL nelle autoclavi.

Utilizza OR-Tools per ottimizzare il posizionamento degli ODL considerando:
- Compatibilità dei cicli di cura
- Dimensioni dei tool
- Capacità delle autoclavi
- Efficienza di utilizzo dello spazio
- Parametri regolabili per distanze e margini di sicurezza
- Posizionamento geometrico reale con coordinate x,y
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
import math

# Importazioni dei modelli
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.nesting_result import NestingResult
from models.tool import Tool
from models.parte import Parte
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura

# Configurazione logging
logger = logging.getLogger(__name__)


class ToolPlacement:
    """
    Classe per rappresentare il posizionamento di un tool nel layout
    """
    def __init__(self, odl_id: int, x: float, y: float, width: float, height: float, rotated: bool = False, piano: int = 1):
        self.odl_id = odl_id
        self.x = x  # Posizione x in mm
        self.y = y  # Posizione y in mm
        self.width = width  # Larghezza in mm
        self.height = height  # Altezza in mm
        self.rotated = rotated  # Se il tool è ruotato
        self.piano = piano  # Piano dell'autoclave
    
    def to_dict(self) -> Dict:
        """Converte in dizionario per il database"""
        return {
            'odl_id': self.odl_id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotated': self.rotated,
            'piano': self.piano
        }
    
    def overlaps_with(self, other: 'ToolPlacement') -> bool:
        """Verifica se questo tool si sovrappone con un altro"""
        if self.piano != other.piano:
            return False
        
        return not (
            self.x + self.width <= other.x or
            other.x + other.width <= self.x or
            self.y + self.height <= other.y or
            other.y + other.height <= self.y
        )


class BinPackingOptimizer:
    """
    Implementa algoritmi di bin packing per il posizionamento ottimale dei tool
    """
    
    def __init__(self, container_width: float, container_height: float, padding: float = 10.0):
        self.container_width = container_width
        self.container_height = container_height
        self.padding = padding
        self.placements: List[ToolPlacement] = []
    
    def can_place_at_position(self, x: float, y: float, width: float, height: float, odl_id: int, piano: int = 1) -> bool:
        """
        Verifica se un tool può essere posizionato in una specifica posizione
        """
        # Verifica se il tool resta dentro i confini del contenitore
        if x + width > self.container_width or y + height > self.container_height:
            return False
        
        # Verifica se si sovrappone con altri tool già posizionati
        temp_placement = ToolPlacement(odl_id, x, y, width, height, piano=piano)
        for placement in self.placements:
            if temp_placement.overlaps_with(placement):
                return False
        
        return True
    
    def find_best_position(self, width: float, height: float, odl_id: int, piano: int = 1) -> Optional[Tuple[float, float]]:
        """
        Trova la migliore posizione per un tool usando l'algoritmo Bottom-Left-Fill
        """
        best_x, best_y = None, None
        best_waste = float('inf')
        
        # Prova tutte le posizioni possibili con un grid search ottimizzato
        step = 5  # Step di 5mm per ottimizzare le performance
        
        for y in range(0, int(self.container_height - height) + 1, step):
            for x in range(0, int(self.container_width - width) + 1, step):
                if self.can_place_at_position(x, y, width, height, odl_id, piano):
                    # Calcola il "waste" - preferisce posizioni più in basso a sinistra
                    waste = y * self.container_width + x
                    
                    if waste < best_waste:
                        best_waste = waste
                        best_x, best_y = x, y
        
        return (best_x, best_y) if best_x is not None else None
    
    def try_rotated_placement(self, width: float, height: float, odl_id: int, piano: int = 1) -> Optional[Tuple[float, float, bool]]:
        """
        Prova il posizionamento normale e ruotato, restituisce il migliore
        """
        # Prova posizionamento normale
        normal_pos = self.find_best_position(width, height, odl_id, piano)
        
        # Prova posizionamento ruotato (se le dimensioni sono diverse)
        rotated_pos = None
        if width != height:
            rotated_pos = self.find_best_position(height, width, odl_id, piano)
        
        # Scegli il migliore (preferisci quello più in basso a sinistra)
        if normal_pos and rotated_pos:
            normal_waste = normal_pos[1] * self.container_width + normal_pos[0]
            rotated_waste = rotated_pos[1] * self.container_width + rotated_pos[0]
            
            if rotated_waste < normal_waste:
                return (rotated_pos[0], rotated_pos[1], True)
            else:
                return (normal_pos[0], normal_pos[1], False)
        elif normal_pos:
            return (normal_pos[0], normal_pos[1], False)
        elif rotated_pos:
            return (rotated_pos[0], rotated_pos[1], True)
        
        return None
    
    def place_tool(self, odl_id: int, width: float, height: float, piano: int = 1) -> bool:
        """
        Posiziona un tool nel contenitore
        """
        # Aggiungi padding alle dimensioni
        padded_width = width + self.padding
        padded_height = height + self.padding
        
        result = self.try_rotated_placement(padded_width, padded_height, odl_id, piano)
        
        if result:
            x, y, rotated = result
            final_width = padded_height if rotated else padded_width
            final_height = padded_width if rotated else padded_height
            
            placement = ToolPlacement(
                odl_id=odl_id,
                x=x,
                y=y,
                width=final_width,
                height=final_height,
                rotated=rotated,
                piano=piano
            )
            
            self.placements.append(placement)
            logger.debug(f"Tool ODL {odl_id} posizionato a ({x:.1f}, {y:.1f}) - {final_width:.1f}x{final_height:.1f}mm" + 
                        (" (ruotato)" if rotated else ""))
            return True
        
        logger.debug(f"Impossibile posizionare tool ODL {odl_id} - {padded_width:.1f}x{padded_height:.1f}mm")
        return False
    
    def get_placements(self) -> List[ToolPlacement]:
        """Restituisce tutti i posizionamenti"""
        return self.placements
    
    def calculate_efficiency(self) -> float:
        """Calcola l'efficienza di utilizzo dello spazio"""
        if not self.placements:
            return 0.0
        
        total_tool_area = sum(p.width * p.height for p in self.placements)
        container_area = self.container_width * self.container_height
        
        return (total_tool_area / container_area) * 100 if container_area > 0 else 0.0


class NestingParameters:
    """
    Classe per gestire i parametri regolabili dell'algoritmo di nesting.
    """
    def __init__(
        self,
        distanza_minima_tool_cm: float = 2.0,
        padding_bordo_autoclave_cm: float = 1.5,
        margine_sicurezza_peso_percent: float = 10.0,
        priorita_minima: int = 1,
        efficienza_minima_percent: float = 60.0
    ):
        self.distanza_minima_tool_cm = distanza_minima_tool_cm
        self.padding_bordo_autoclave_cm = padding_bordo_autoclave_cm
        self.margine_sicurezza_peso_percent = margine_sicurezza_peso_percent
        self.priorita_minima = priorita_minima
        self.efficienza_minima_percent = efficienza_minima_percent
    
    @classmethod
    def from_dict(cls, params_dict: Dict) -> 'NestingParameters':
        """Crea un'istanza dai parametri del dizionario"""
        return cls(
            distanza_minima_tool_cm=params_dict.get('distanza_minima_tool_cm', 2.0),
            padding_bordo_autoclave_cm=params_dict.get('padding_bordo_autoclave_cm', 1.5),
            margine_sicurezza_peso_percent=params_dict.get('margine_sicurezza_peso_percent', 10.0),
            priorita_minima=params_dict.get('priorita_minima', 1),
            efficienza_minima_percent=params_dict.get('efficienza_minima_percent', 60.0)
        )


class NestingOptimizer:
    """
    Classe per l'ottimizzazione del nesting degli ODL nelle autoclavi.
    """
    
    def __init__(self, db: Session, parameters: Optional[NestingParameters] = None):
        self.db = db
        self.parameters = parameters or NestingParameters()
        logger.info(f"NestingOptimizer inizializzato con parametri: "
                   f"distanza_tool={self.parameters.distanza_minima_tool_cm}cm, "
                   f"padding_bordo={self.parameters.padding_bordo_autoclave_cm}cm, "
                   f"margine_peso={self.parameters.margine_sicurezza_peso_percent}%")
        
    def get_compatible_odl_groups(self) -> Dict[str, List[ODL]]:
        """
        Raggruppa gli ODL in attesa per ciclo di cura compatibile.
        Filtra per priorità minima se specificata nei parametri.
        
        Returns:
            Dict[str, List[ODL]]: Dizionario con chiave il ciclo di cura e valore la lista degli ODL
        """
        # Recupera tutti gli ODL in stato "Attesa Cura" con priorità >= priorità minima
        # Include le relazioni necessarie per evitare query aggiuntive
        query = self.db.query(ODL).filter(
            ODL.status == "Attesa Cura",
            ODL.priorita >= self.parameters.priorita_minima
        ).join(ODL.parte).join(Parte.ciclo_cura).join(ODL.tool)
        
        odl_in_coda = query.all()
        
        logger.info(f"Query ODL: trovati {len(odl_in_coda)} ODL in 'Attesa Cura' con priorità >= {self.parameters.priorita_minima}")
        
        # Raggruppa per ciclo di cura
        groups = {}
        for odl in odl_in_coda:
            if odl.parte and odl.parte.ciclo_cura:
                # Usa il nome del ciclo di cura come chiave
                ciclo_key = odl.parte.ciclo_cura.nome
                if ciclo_key not in groups:
                    groups[ciclo_key] = []
                groups[ciclo_key].append(odl)
                logger.debug(f"ODL {odl.id} aggiunto al gruppo '{ciclo_key}' (priorità {odl.priorita})")
            else:
                logger.warning(f"ODL {odl.id} non ha parte o ciclo di cura associato, saltato")
        
        logger.info(f"Trovati {len(groups)} gruppi di ODL compatibili: {list(groups.keys())}")
        for ciclo_key, odl_list in groups.items():
            logger.info(f"  - {ciclo_key}: {len(odl_list)} ODL")
        
        return groups
    
    def get_available_autoclaves(self) -> List[Autoclave]:
        """
        Recupera tutte le autoclavi disponibili per il nesting.
        
        Returns:
            List[Autoclave]: Lista delle autoclavi disponibili
        """
        autoclaves = self.db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        logger.info(f"Trovate {len(autoclaves)} autoclavi disponibili")
        return autoclaves
    
    def calculate_tool_dimensions(self, odl: ODL) -> Tuple[float, float, float]:
        """
        Calcola le dimensioni del tool associato all'ODL considerando le distanze minime.
        
        Args:
            odl: L'ODL di cui calcolare le dimensioni
            
        Returns:
            Tuple[float, float, float]: (larghezza, lunghezza, peso) in mm e kg
        """
        if not odl.tool:
            return (0.0, 0.0, 0.0)
        
        # Dimensioni del tool in mm
        base_width = odl.tool.larghezza_piano or 100.0  # Default se non specificato
        base_length = odl.tool.lunghezza_piano or 100.0  # Default se non specificato
        
        # Aggiungi la distanza minima tra tool (convertita da cm a mm)
        distanza_mm = self.parameters.distanza_minima_tool_cm * 10
        width = base_width + distanza_mm
        length = base_length + distanza_mm
        
        # Peso stimato basato sul materiale e dimensioni
        # Formula semplificata: volume * densità stimata
        volume_cm3 = (base_width * base_length * 10) / 1000  # Assumiamo spessore 10mm
        peso_kg = volume_cm3 * 0.002  # Densità stimata 2g/cm³
        
        return (width, length, peso_kg)
    
    def calculate_effective_autoclave_area(self, autoclave: Autoclave) -> float:
        """
        Calcola l'area effettiva dell'autoclave considerando il padding dal bordo.
        
        Args:
            autoclave: L'autoclave di cui calcolare l'area effettiva
            
        Returns:
            float: Area effettiva in cm²
        """
        if not autoclave.lunghezza or not autoclave.larghezza_piano:
            return 0.0
        
        # Converti padding da cm a mm per il calcolo
        padding_mm = self.parameters.padding_bordo_autoclave_cm * 10
        
        # Calcola dimensioni effettive sottraendo il padding da entrambi i lati
        effective_length = max(0, autoclave.lunghezza - (2 * padding_mm))
        effective_width = max(0, autoclave.larghezza_piano - (2 * padding_mm))
        
        # Converti in cm² per coerenza con il resto del sistema
        effective_area_cm2 = (effective_length * effective_width) / 100
        
        logger.debug(f"Autoclave {autoclave.nome}: area originale={autoclave.area_piano}cm², "
                    f"area effettiva={effective_area_cm2}cm² (padding={self.parameters.padding_bordo_autoclave_cm}cm)")
        
        return effective_area_cm2

    def can_fit_in_autoclave(self, odl_list: List[ODL], autoclave: Autoclave) -> bool:
        """
        Verifica se una lista di ODL può essere inserita in un'autoclave.
        Considera i parametri di padding e margine di sicurezza.
        
        Args:
            odl_list: Lista degli ODL da verificare
            autoclave: L'autoclave in cui inserire gli ODL
            
        Returns:
            bool: True se gli ODL possono essere inseriti, False altrimenti
        """
        if not autoclave.lunghezza or not autoclave.larghezza_piano:
            return False
        
        total_area = 0.0
        total_weight = 0.0
        
        for odl in odl_list:
            width, length, weight = self.calculate_tool_dimensions(odl)
            total_area += (width * length) / 100  # Conversione in cm²
            total_weight += weight
        
        # Verifica area disponibile (considerando il padding)
        effective_area = self.calculate_effective_autoclave_area(autoclave)
        if total_area > effective_area:
            logger.debug(f"Area insufficiente: richiesta={total_area}cm², disponibile={effective_area}cm²")
            return False
        
        # Verifica peso massimo (considerando il margine di sicurezza)
        if autoclave.max_load_kg:
            max_weight_with_margin = autoclave.max_load_kg * (1 - self.parameters.margine_sicurezza_peso_percent / 100)
            if total_weight > max_weight_with_margin:
                logger.debug(f"Peso eccessivo: richiesto={total_weight}kg, "
                           f"limite con margine={max_weight_with_margin}kg")
                return False
        
        return True
    
    def optimize_single_plane_nesting(self, odl_group: List[ODL], autoclave: Autoclave) -> Optional[Dict]:
        """
        Ottimizza il nesting per un singolo piano usando bin packing geometrico reale.
        Calcola le posizioni specifiche x,y per ogni tool.
        
        Args:
            odl_group: Lista degli ODL da ottimizzare
            autoclave: L'autoclave target
            
        Returns:
            Optional[Dict]: Risultato dell'ottimizzazione con posizioni reali o None se non possibile
        """
        if not odl_group or not autoclave:
            return None
        
        logger.info(f"Inizio ottimizzazione nesting per {len(odl_group)} ODL in autoclave {autoclave.nome}")
        
        # Calcola le dimensioni effettive dell'autoclave considerando i bordi
        padding_bordo_mm = self.parameters.padding_bordo_autoclave_cm * 10
        effective_width = autoclave.lunghezza - (2 * padding_bordo_mm)
        effective_height = autoclave.larghezza_piano - (2 * padding_bordo_mm)
        
        if effective_width <= 0 or effective_height <= 0:
            logger.error(f"Dimensioni effettive autoclave non valide: {effective_width}x{effective_height}mm")
            return None
        
        # Inizializza il bin packing optimizer
        padding_mm = self.parameters.distanza_minima_tool_cm * 10
        bin_packer = BinPackingOptimizer(
            container_width=effective_width,
            container_height=effective_height,
            padding=padding_mm
        )
        
        # Ordina gli ODL per priorità decrescente e poi per area decrescente
        sorted_odl = sorted(odl_group, key=lambda x: (
            -x.priorita,  # Priorità più alta prima
            -self.calculate_tool_dimensions(x)[0] * self.calculate_tool_dimensions(x)[1]  # Area più grande prima
        ))
        
        selected_odl = []
        excluded_odl = []
        exclusion_reasons = []
        total_weight = 0.0
        
        # Calcola il peso massimo considerando il margine di sicurezza
        max_weight = autoclave.max_load_kg or float('inf')
        if autoclave.max_load_kg:
            max_weight = autoclave.max_load_kg * (1 - self.parameters.margine_sicurezza_peso_percent / 100)
        
        # Prova a posizionare ogni ODL
        for odl in sorted_odl:
            if not odl.tool:
                excluded_odl.append(odl)
                exclusion_reasons.append(f"ODL {odl.id}: Tool non trovato")
                continue
            
            # Ottieni le dimensioni del tool
            tool_width = odl.tool.lunghezza_piano or 100.0  # Lunghezza = larghezza nel piano
            tool_height = odl.tool.larghezza_piano or 100.0  # Larghezza = altezza nel piano
            
            # Calcola il peso stimato
            _, _, tool_weight = self.calculate_tool_dimensions(odl)
            
            # Verifica vincolo di peso
            if total_weight + tool_weight > max_weight:
                excluded_odl.append(odl)
                exclusion_reasons.append(f"ODL {odl.id}: Peso eccessivo (richiesto: {tool_weight:.1f}kg, disponibile: {max_weight - total_weight:.1f}kg)")
                continue
            
            # Prova a posizionare il tool
            if bin_packer.place_tool(odl.id, tool_width, tool_height, piano=1):
                selected_odl.append(odl)
                total_weight += tool_weight
                logger.debug(f"ODL {odl.id} posizionato con successo")
            else:
                excluded_odl.append(odl)
                exclusion_reasons.append(f"ODL {odl.id}: Spazio geometrico insufficiente ({tool_width:.1f}x{tool_height:.1f}mm)")
                logger.debug(f"ODL {odl.id} escluso per mancanza di spazio geometrico")
        
        if not selected_odl:
            logger.info("Nessun ODL selezionato per il nesting")
            return None
        
        # Calcola efficienza geometrica
        geometric_efficiency = bin_packer.calculate_efficiency()
        
        # Verifica se l'efficienza soddisfa il requisito minimo
        if geometric_efficiency < self.parameters.efficienza_minima_percent:
            logger.debug(f"Efficienza geometrica {geometric_efficiency:.1f}% inferiore al minimo richiesto {self.parameters.efficienza_minima_percent}%")
            return None
        
        # Ottieni le posizioni calcolate
        tool_positions = bin_packer.get_placements()
        
        # Aggiusta le posizioni considerando l'offset del bordo
        adjusted_positions = []
        for pos in tool_positions:
            adjusted_pos = ToolPlacement(
                odl_id=pos.odl_id,
                x=pos.x + padding_bordo_mm,  # Aggiungi offset bordo
                y=pos.y + padding_bordo_mm,  # Aggiungi offset bordo
                width=pos.width - padding_mm,  # Rimuovi padding interno
                height=pos.height - padding_mm,  # Rimuovi padding interno
                rotated=pos.rotated,
                piano=pos.piano
            )
            adjusted_positions.append(adjusted_pos)
        
        # Calcola statistiche finali
        total_tool_area = sum(pos.width * pos.height for pos in adjusted_positions)
        autoclave_area = autoclave.lunghezza * autoclave.larghezza_piano
        overall_efficiency = (total_tool_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        
        logger.info(f"Nesting completato: {len(selected_odl)} ODL posizionati, "
                   f"efficienza geometrica {geometric_efficiency:.1f}%, "
                   f"efficienza totale {overall_efficiency:.1f}%, "
                   f"peso {total_weight:.1f}/{max_weight:.1f}kg")
        
        return {
            'selected_odl': selected_odl,
            'excluded_odl': excluded_odl,
            'exclusion_reasons': exclusion_reasons,
            'tool_positions': [pos.to_dict() for pos in adjusted_positions],  # NUOVO: posizioni reali
            'total_weight': total_weight,
            'geometric_efficiency': geometric_efficiency,  # Efficienza del bin packing
            'overall_efficiency': overall_efficiency,      # Efficienza rispetto all'autoclave totale
            'autoclave': autoclave,
            'effective_dimensions': {
                'width': effective_width,
                'height': effective_height,
                'border_padding_mm': padding_bordo_mm,
                'tool_padding_mm': padding_mm
            },
            'max_weight_with_margin': max_weight,
            'parameters_used': {
                'distanza_minima_tool_cm': self.parameters.distanza_minima_tool_cm,
                'padding_bordo_autoclave_cm': self.parameters.padding_bordo_autoclave_cm,
                'margine_sicurezza_peso_percent': self.parameters.margine_sicurezza_peso_percent,
                'efficienza_minima_percent': self.parameters.efficienza_minima_percent
            }
        }


def compute_nesting(db: Session, odl_ids: List[int], autoclave_id: int, parameters: Optional[Dict] = None) -> Dict:
    """
    Funzione di compatibilità per il codice esistente.
    
    Args:
        db: Sessione del database
        odl_ids: Lista degli ID degli ODL
        autoclave_id: ID dell'autoclave
        parameters: Parametri opzionali per l'algoritmo di nesting
        
    Returns:
        Dict: Risultato del nesting con posizioni reali
    """
    # Crea i parametri se forniti
    nesting_params = None
    if parameters:
        nesting_params = NestingParameters.from_dict(parameters)
    
    optimizer = NestingOptimizer(db, nesting_params)
    
    # Recupera gli ODL e l'autoclave
    odl_list = db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
    autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
    
    if not autoclave:
        return {'error': 'Autoclave non trovata'}
    
    result = optimizer.optimize_single_plane_nesting(odl_list, autoclave)
    
    if not result:
        return {'error': 'Impossibile ottimizzare il nesting o efficienza insufficiente'}
    
    return {
        'success': True,
        'selected_odl_ids': [odl.id for odl in result['selected_odl']],
        'excluded_odl_ids': [odl.id for odl in result['excluded_odl']],
        'exclusion_reasons': result['exclusion_reasons'],
        'tool_positions': result['tool_positions'],  # NUOVO: posizioni reali
        'total_weight': result['total_weight'],
        'geometric_efficiency': result['geometric_efficiency'],  # Efficienza geometrica
        'overall_efficiency': result['overall_efficiency'],      # Efficienza totale
        'effective_dimensions': result['effective_dimensions'],   # Dimensioni effettive
        'autoclave_info': {
            'id': autoclave.id,
            'nome': autoclave.nome,
            'lunghezza': autoclave.lunghezza,
            'larghezza_piano': autoclave.larghezza_piano,
            'area_piano': autoclave.area_piano
        },
        'parameters_used': result.get('parameters_used')
    }


def generate_automatic_nesting(db: Session, parameters: Optional[Dict] = None) -> Dict:
    """
    Genera automaticamente il nesting ottimale per tutti gli ODL in attesa.
    
    Args:
        db: Sessione del database
        parameters: Parametri opzionali per l'algoritmo di nesting
        
    Returns:
        Dict: Risultato della generazione automatica con dettagli del nesting
    """
    # Crea i parametri se forniti
    nesting_params = None
    if parameters:
        nesting_params = NestingParameters.from_dict(parameters)
    
    optimizer = NestingOptimizer(db, nesting_params)
    
    try:
        # 1. Raggruppa gli ODL per ciclo compatibile
        odl_groups = optimizer.get_compatible_odl_groups()
        
        if not odl_groups:
            return {
                'success': False,
                'message': 'Nessun ODL in attesa trovato con i parametri specificati',
                'nesting_results': [],
                'parameters_used': nesting_params.__dict__ if nesting_params else None
            }
        
        # 2. Recupera le autoclavi disponibili
        available_autoclaves = optimizer.get_available_autoclaves()
        
        if not available_autoclaves:
            return {
                'success': False,
                'message': 'Nessuna autoclave disponibile',
                'nesting_results': [],
                'parameters_used': nesting_params.__dict__ if nesting_params else None
            }
        
        nesting_results = []
        total_odl_processed = 0
        total_odl_excluded = 0
        
        # 3. Per ogni gruppo di ODL compatibili
        for ciclo_key, odl_list in odl_groups.items():
            logger.info(f"Processando gruppo {ciclo_key} con {len(odl_list)} ODL")
            
            # Prova ogni autoclave disponibile
            best_result = None
            best_efficiency = 0
            
            for autoclave in available_autoclaves:
                result = optimizer.optimize_single_plane_nesting(odl_list, autoclave)
                
                if result and result['overall_efficiency'] > best_efficiency:
                    best_result = result
                    best_efficiency = result['overall_efficiency']
            
            # Se trovato un risultato valido, crea il NestingResult
            if best_result:
                # Prepara le note con i metadati dell'algoritmo
                algorithm_metadata = {
                    'tool_positions': best_result['tool_positions'],
                    'effective_dimensions': best_result['effective_dimensions'],
                    'geometric_efficiency': best_result['geometric_efficiency'],
                    'overall_efficiency': best_result['overall_efficiency'],
                    'parameters_used': best_result['parameters_used']
                }
                
                note_text = f"Nesting automatico generato per ciclo {ciclo_key} con parametri personalizzati\n"
                note_text += f"Algoritmo: Bin Packing Bottom-Left-Fill\n"
                note_text += f"Efficienza geometrica: {best_result['geometric_efficiency']:.1f}%\n"
                note_text += f"Efficienza totale: {best_result['overall_efficiency']:.1f}%\n"
                
                # Crea il record nel database
                nesting_result = NestingResult(
                    autoclave_id=best_result['autoclave'].id,
                    odl_ids=[odl.id for odl in best_result['selected_odl']],
                    odl_esclusi_ids=[odl.id for odl in best_result['excluded_odl']],
                    motivi_esclusione=best_result['exclusion_reasons'],
                    stato="Bozza",  # Stato iniziale
                    area_utilizzata=sum(pos['width'] * pos['height'] for pos in best_result['tool_positions']) / 10000,  # Converti mm² in cm²
                    area_totale=best_result['autoclave'].area_piano or 0.0,
                    peso_totale_kg=best_result['total_weight'],
                    area_piano_1=sum(pos['width'] * pos['height'] for pos in best_result['tool_positions'] if pos['piano'] == 1) / 10000,
                    area_piano_2=sum(pos['width'] * pos['height'] for pos in best_result['tool_positions'] if pos['piano'] == 2) / 10000,
                    posizioni_tool=best_result['tool_positions'],  # NUOVO: salva le posizioni reali
                    note=note_text,
                    created_at=datetime.now()
                )
                
                db.add(nesting_result)
                db.commit()
                db.refresh(nesting_result)
                
                # Aggiorna lo stato degli ODL selezionati
                for odl in best_result['selected_odl']:
                    odl.status = "Attesa Cura"
                    db.add(odl)
                
                db.commit()
                
                nesting_results.append({
                    'id': nesting_result.id,
                    'autoclave_id': nesting_result.autoclave_id,
                    'autoclave_nome': best_result['autoclave'].nome,
                    'ciclo_cura': ciclo_key,
                    'odl_inclusi': len(best_result['selected_odl']),
                    'odl_esclusi': len(best_result['excluded_odl']),
                    'efficienza_geometrica': round(best_result['geometric_efficiency'], 2),  # NUOVO
                    'efficienza_totale': round(best_result['overall_efficiency'], 2),         # NUOVO
                    'area_utilizzata': round(nesting_result.area_utilizzata, 2),
                    'area_totale': round(nesting_result.area_totale, 2),
                    'peso_totale': round(best_result['total_weight'], 2),
                    'peso_massimo_con_margine': round(best_result.get('max_weight_with_margin', 0), 2),
                    'tool_positions_count': len(best_result['tool_positions']),  # NUOVO
                    'stato': 'Bozza',
                    'parameters_used': best_result.get('parameters_used')
                })
                
                total_odl_processed += len(best_result['selected_odl'])
                total_odl_excluded += len(best_result['excluded_odl'])
                
                logger.info(f"Creato nesting {nesting_result.id} per autoclave {best_result['autoclave'].nome}")
        
        return {
            'success': True,
            'message': f'Generati {len(nesting_results)} nesting automatici con parametri personalizzati',
            'nesting_results': nesting_results,
            'summary': {
                'total_nesting_created': len(nesting_results),
                'total_odl_processed': total_odl_processed,
                'total_odl_excluded': total_odl_excluded,
                'autoclavi_utilizzate': len(set(nr['autoclave_id'] for nr in nesting_results))
            },
            'parameters_used': nesting_params.__dict__ if nesting_params else None
        }
        
    except Exception as e:
        logger.error(f"Errore durante la generazione automatica del nesting: {str(e)}")
        db.rollback()
        return {
            'success': False,
            'message': f'Errore durante la generazione: {str(e)}',
            'nesting_results': [],
            'parameters_used': nesting_params.__dict__ if nesting_params else None
        } 