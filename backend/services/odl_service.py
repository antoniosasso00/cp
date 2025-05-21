from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models.odl import ODL, ODLStatus, ODLPhase
from ..models.part import Part
from ..schemas.odl import ODLCreate, ODLUpdate, PartInODL

class ODLService:
    def __init__(self, db: Session):
        self.db = db

    def create_odl(self, odl_data: ODLCreate) -> ODL:
        """Crea un nuovo ODL con le parti specificate"""
        # Verifica che tutte le parti esistano e abbiano un tool assegnato
        for part_data in odl_data.parts:
            part = self.db.query(Part).filter(Part.id == part_data.part_id).first()
            if not part:
                raise ValueError(f"Parte con ID {part_data.part_id} non trovata")
            if not part.tool:
                raise ValueError(f"Parte {part.part_number} non ha un tool assegnato")

        # Crea l'ODL
        odl = ODL(
            code=odl_data.code,
            description=odl_data.description,
            status=ODLStatus.CREATED,
            current_phase=ODLPhase.LAMINAZIONE
        )
        self.db.add(odl)
        self.db.flush()

        # Aggiungi le parti all'ODL
        for part_data in odl_data.parts:
            part = self.db.query(Part).filter(Part.id == part_data.part_id).first()
            odl.parts.append(part)
            # Aggiorna lo stato della parte
            part.status = "in_odl"
            part.last_updated = datetime.utcnow()

        self.db.commit()
        self.db.refresh(odl)
        return odl

    def get_odl(self, odl_id: int) -> Optional[ODL]:
        """Recupera un ODL specifico con tutti i dettagli"""
        return self.db.query(ODL).filter(ODL.id == odl_id).first()

    def update_odl(self, odl_id: int, odl_data: ODLUpdate) -> Optional[ODL]:
        """Aggiorna un ODL esistente"""
        odl = self.get_odl(odl_id)
        if not odl:
            return None

        for field, value in odl_data.dict(exclude_unset=True).items():
            setattr(odl, field, value)

        odl.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(odl)
        return odl

    def advance_phase(self, odl_id: int) -> Optional[ODL]:
        """Avanza l'ODL alla fase successiva se possibile"""
        odl = self.get_odl(odl_id)
        if not odl:
            return None

        # Verifica che tutte le parti siano pronte per la fase successiva
        current_phase = odl.current_phase
        next_phase = self._get_next_phase(current_phase)
        
        if not next_phase:
            raise ValueError("ODL già completato")

        # Verifica lo stato delle parti
        for part in odl.parts:
            if not self._can_advance_part(part, current_phase):
                raise ValueError(f"Parte {part.part_number} non è pronta per la fase {next_phase}")

        # Aggiorna la fase
        odl.current_phase = next_phase
        odl.updated_at = datetime.utcnow()

        # Aggiorna lo stato delle parti
        for part in odl.parts:
            part.status = f"in_{next_phase}"
            part.last_updated = datetime.utcnow()

        self.db.commit()
        self.db.refresh(odl)
        return odl

    def _get_next_phase(self, current_phase: ODLPhase) -> Optional[ODLPhase]:
        """Determina la fase successiva"""
        phases = list(ODLPhase)
        try:
            current_index = phases.index(current_phase)
            if current_index < len(phases) - 1:
                return phases[current_index + 1]
        except ValueError:
            pass
        return None

    def _can_advance_part(self, part: Part, current_phase: ODLPhase) -> bool:
        """Verifica se una parte può avanzare alla fase successiva"""
        # Implementa la logica di validazione per ogni fase
        if current_phase == ODLPhase.LAMINAZIONE:
            return part.status == "laminated"
        elif current_phase == ODLPhase.PRE_NESTING:
            return part.status == "ready_for_nesting"
        elif current_phase == ODLPhase.NESTING:
            return part.status == "nested"
        elif current_phase == ODLPhase.AUTOCLAVE:
            return part.status == "ready_for_autoclave"
        return False

    def list_odls(self, skip: int = 0, limit: int = 100) -> List[ODL]:
        """Lista tutti gli ODL con paginazione"""
        return self.db.query(ODL).offset(skip).limit(limit).all() 