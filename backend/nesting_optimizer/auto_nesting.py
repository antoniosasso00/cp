"""
Modulo per l'ottimizzazione automatica del nesting degli ODL nelle autoclavi.

Utilizza OR-Tools per ottimizzare il posizionamento degli ODL considerando:
- Compatibilità dei cicli di cura
- Dimensioni dei tool
- Capacità delle autoclavi
- Efficienza di utilizzo dello spazio
- Parametri regolabili per distanze e margini di sicurezza
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging

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
        Ottimizza il nesting per un singolo piano usando un algoritmo greedy.
        Considera i parametri di efficienza minima e margini di sicurezza.
        
        Args:
            odl_group: Lista degli ODL da ottimizzare
            autoclave: L'autoclave target
            
        Returns:
            Optional[Dict]: Risultato dell'ottimizzazione o None se non possibile
        """
        if not odl_group or not autoclave:
            return None
        
        # Ordina gli ODL per priorità decrescente e poi per area decrescente
        sorted_odl = sorted(odl_group, key=lambda x: (
            -x.priorita,  # Priorità più alta prima
            -self.calculate_tool_dimensions(x)[0] * self.calculate_tool_dimensions(x)[1]  # Area più grande prima
        ))
        
        selected_odl = []
        total_area = 0.0
        total_weight = 0.0
        excluded_odl = []
        exclusion_reasons = []
        
        # Usa l'area effettiva considerando il padding
        effective_area = self.calculate_effective_autoclave_area(autoclave)
        
        # Calcola il peso massimo considerando il margine di sicurezza
        max_weight = autoclave.max_load_kg or float('inf')
        if autoclave.max_load_kg:
            max_weight = autoclave.max_load_kg * (1 - self.parameters.margine_sicurezza_peso_percent / 100)
        
        for odl in sorted_odl:
            width, length, weight = self.calculate_tool_dimensions(odl)
            area = (width * length) / 100  # Conversione in cm²
            
            # Verifica se l'ODL può essere aggiunto
            if (total_area + area <= effective_area and 
                total_weight + weight <= max_weight):
                selected_odl.append(odl)
                total_area += area
                total_weight += weight
            else:
                excluded_odl.append(odl)
                if total_area + area > effective_area:
                    exclusion_reasons.append(f"ODL {odl.id}: Area insufficiente (richiesta: {area:.1f}cm², disponibile: {effective_area - total_area:.1f}cm²)")
                else:
                    exclusion_reasons.append(f"ODL {odl.id}: Peso eccessivo (richiesto: {weight:.1f}kg, disponibile: {max_weight - total_weight:.1f}kg)")
        
        if not selected_odl:
            return None
        
        # Calcola efficienza rispetto all'area effettiva
        efficiency = (total_area / effective_area) * 100 if effective_area > 0 else 0
        
        # Verifica se l'efficienza soddisfa il requisito minimo
        if efficiency < self.parameters.efficienza_minima_percent:
            logger.debug(f"Efficienza {efficiency:.1f}% inferiore al minimo richiesto {self.parameters.efficienza_minima_percent}%")
            return None
        
        logger.info(f"Nesting ottimizzato: {len(selected_odl)} ODL, efficienza {efficiency:.1f}%, "
                   f"area {total_area:.1f}/{effective_area:.1f}cm², peso {total_weight:.1f}/{max_weight:.1f}kg")
        
        return {
            'selected_odl': selected_odl,
            'excluded_odl': excluded_odl,
            'exclusion_reasons': exclusion_reasons,
            'total_area': total_area,
            'total_weight': total_weight,
            'efficiency': efficiency,
            'autoclave': autoclave,
            'effective_area': effective_area,
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
        Dict: Risultato del nesting
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
        'total_area': result['total_area'],
        'total_weight': result['total_weight'],
        'efficiency': result['efficiency'],
        'effective_area': result.get('effective_area'),
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
                
                if result and result['efficiency'] > best_efficiency:
                    best_result = result
                    best_efficiency = result['efficiency']
            
            # Se trovato un risultato valido, crea il NestingResult
            if best_result:
                # Crea il record nel database
                nesting_result = NestingResult(
                    autoclave_id=best_result['autoclave'].id,
                    odl_ids=[odl.id for odl in best_result['selected_odl']],
                    odl_esclusi_ids=[odl.id for odl in best_result['excluded_odl']],
                    motivi_esclusione=best_result['exclusion_reasons'],
                    stato="Bozza",  # Stato iniziale
                    area_utilizzata=best_result['total_area'],
                    area_totale=best_result.get('effective_area', best_result['autoclave'].area_piano),
                    peso_totale_kg=best_result['total_weight'],
                    area_piano_1=best_result['total_area'],
                    area_piano_2=0.0,  # Piano singolo
                    note=f"Nesting automatico generato per ciclo {ciclo_key} con parametri personalizzati",
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
                    'efficienza': round(best_result['efficiency'], 2),
                    'area_utilizzata': round(best_result['total_area'], 2),
                    'area_effettiva': round(best_result.get('effective_area', 0), 2),
                    'peso_totale': round(best_result['total_weight'], 2),
                    'peso_massimo_con_margine': round(best_result.get('max_weight_with_margin', 0), 2),
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