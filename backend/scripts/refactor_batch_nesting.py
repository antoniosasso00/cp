#!/usr/bin/env python3
"""
Script per ristrutturare batch_nesting.py in moduli separati
"""

import os
import shutil
from pathlib import Path

def create_backup():
    """Crea backup del file originale"""
    source = Path("backend/api/routers/batch_nesting.py")
    backup = Path("backend/api/routers/batch_nesting_backup.py")
    shutil.copy2(source, backup)
    print(f"✅ Backup creato: {backup}")

def create_directories():
    """Crea strutture directory"""
    dirs = [
        "backend/services/batch",
        "backend/schemas/batch", 
        "backend/utils/batch"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        print(f"📁 Creato: {dir_path}")

def create_crud_router():
    """Crea router CRUD base"""
    content = '''"""
Router CRUD base per batch nesting
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ...database import get_db
from ...models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from ...schemas.batch_nesting import (
    BatchNestingCreate, 
    BatchNestingResponse, 
    BatchNestingUpdate, 
    BatchNestingList
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting - CRUD"]
)

@router.post("/", response_model=BatchNestingResponse, status_code=status.HTTP_201_CREATED)
def create_batch_nesting(batch_data: BatchNestingCreate, db: Session = Depends(get_db)):
    """Crea un nuovo batch nesting - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.get("/", response_model=List[BatchNestingList])
def read_batch_nesting_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Lista batch nesting - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.get("/{batch_id}", response_model=BatchNestingResponse)
def read_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """Ottiene singolo batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.put("/{batch_id}", response_model=BatchNestingResponse)
def update_batch_nesting(
    batch_id: str, 
    batch_update: BatchNestingUpdate, 
    db: Session = Depends(get_db)
):
    """Aggiorna batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_nesting(batch_id: str, db: Session = Depends(get_db)):
    """Elimina batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass
'''
    
    file_path = Path("backend/api/routers/batch_nesting_crud.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_workflow_router():
    """Crea router workflow stati"""
    content = '''"""
Router workflow gestione stati batch
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...models.batch_nesting import BatchNesting
from ...schemas.batch_nesting import BatchNestingResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting - Workflow"]
)

@router.patch("/{batch_id}/confirm", response_model=BatchNestingResponse)
def confirm_batch_nesting(
    batch_id: str, 
    confermato_da_utente: str = Query(...),
    confermato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Conferma batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.patch("/{batch_id}/load", response_model=BatchNestingResponse)
def load_batch_nesting(
    batch_id: str,
    caricato_da_utente: str = Query(...),
    caricato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Carica batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.patch("/{batch_id}/cure", response_model=BatchNestingResponse)
def cure_batch_nesting(
    batch_id: str,
    avviato_da_utente: str = Query(...),
    avviato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Avvia cura - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.patch("/{batch_id}/terminate", response_model=BatchNestingResponse)
def terminate_batch_nesting(
    batch_id: str,
    terminato_da_utente: str = Query(...),
    terminato_da_ruolo: str = Query(...),
    db: Session = Depends(get_db)
):
    """Termina batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass
'''
    
    file_path = Path("backend/api/routers/batch_nesting_workflow.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_generation_router():
    """Crea router generazione nesting"""
    content = '''"""
Router generazione nesting e algoritmi
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from ...database import get_db

logger = logging.getLogger(__name__)

class NestingParametri(BaseModel):
    padding_mm: int = 1
    min_distance_mm: int = 1

class NestingRequest(BaseModel):
    odl_ids: List[str]
    autoclave_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class NestingMultiRequest(BaseModel):
    odl_ids: List[str]
    parametri: NestingParametri = NestingParametri()

class NestingResponse(BaseModel):
    batch_id: str = ""
    message: str
    success: bool

router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting - Generation"]
)

@router.get("/data")
def get_nesting_data(db: Session = Depends(get_db)):
    """Ottiene dati per nesting - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.post("/genera", response_model=NestingResponse)
def genera_nesting_robusto(request: NestingRequest, db: Session = Depends(get_db)):
    """Genera nesting singolo - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.post("/genera-multi", response_model=Dict[str, Any])
def genera_nesting_multi_batch(request: NestingMultiRequest, db: Session = Depends(get_db)):
    """Genera multi-batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass
'''
    
    file_path = Path("backend/api/routers/batch_nesting_generation.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_results_router():
    """Crea router risultati"""
    content = '''"""
Router risultati e visualizzazione
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting - Results"]
)

@router.get("/result/{batch_id}")
def get_batch_result(batch_id: str, multi: bool = False, db: Session = Depends(get_db)):
    """Risultati batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.get("/{batch_id}/statistics")
def get_batch_statistics(batch_id: str, db: Session = Depends(get_db)):
    """Statistiche batch - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.get("/{batch_id}/validate")
def validate_nesting_layout(batch_id: str, db: Session = Depends(get_db)):
    """Valida layout - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass
'''
    
    file_path = Path("backend/api/routers/batch_nesting_results.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_maintenance_router():
    """Crea router manutenzione"""
    content = '''"""
Router manutenzione e diagnostica
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/batch_nesting",
    tags=["Batch Nesting - Maintenance"]
)

@router.get("/diagnosi-sistema", response_model=Dict[str, Any])
def diagnosi_sistema_multi_batch(db: Session = Depends(get_db)):
    """Diagnosi sistema - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass

@router.delete("/cleanup")
def cleanup_old_batch_nesting(
    days_threshold: int = Query(7, ge=1, le=30),
    stato_filter: Optional[str] = Query("SOSPESO"),
    db: Session = Depends(get_db)
):
    """Cleanup batch vecchi - IMPLEMENTAZIONE DA MIGRARE"""
    # TODO: Migrare implementazione dal file originale
    pass
'''
    
    file_path = Path("backend/api/routers/batch_nesting_maintenance.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_batch_service():
    """Crea servizio business logic"""
    content = '''"""
Servizio business logic batch nesting
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ...models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from ...models.autoclave import Autoclave, StatoAutoclaveEnum
from ...models.odl import ODL

logger = logging.getLogger(__name__)

class BatchService:
    """Servizio per business logic batch nesting"""
    
    @staticmethod
    def create_robust_batch(
        db: Session,
        autoclave_id: str,
        odl_ids: List[str],
        nesting_result: Dict[str, Any]
    ) -> BatchNesting:
        """Crea batch robusto - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
    
    @staticmethod
    def distribute_odls_intelligently(
        autoclavi: List[Autoclave],
        odl_ids: List[str]
    ) -> Dict[str, List[str]]:
        """Distribuisce ODL tra autoclavi - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
    
    @staticmethod
    def validate_batch_data(
        db: Session,
        autoclave_id: str,
        odl_ids: List[str]
    ) -> bool:
        """Valida dati batch - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
'''
    
    file_path = Path("backend/services/batch/batch_service.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_workflow_service():
    """Crea servizio workflow"""
    content = '''"""
Servizio gestione workflow stati batch
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ...models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from ...models.autoclave import Autoclave, StatoAutoclaveEnum
from ...models.odl import ODL

logger = logging.getLogger(__name__)

class BatchWorkflowService:
    """Servizio per gestione workflow stati batch"""
    
    @staticmethod
    def update_odl_states_on_confirm(db: Session, batch: BatchNesting) -> bool:
        """Aggiorna stati ODL su conferma - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
    
    @staticmethod
    def update_autoclave_states(db: Session, autoclave_id: str, new_state: str) -> bool:
        """Aggiorna stato autoclave - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
    
    @staticmethod
    def validate_state_transition(current_state: str, new_state: str) -> bool:
        """Valida transizione di stato - DA IMPLEMENTARE"""
        # TODO: Migrare logica dal file originale
        pass
'''
    
    file_path = Path("backend/services/batch/batch_workflow_service.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def create_main_router():
    """Crea router principale modulare"""
    content = '''"""
Router principale batch_nesting.py - Versione modulare

Aggrega tutti i router specializzati mantenendo compatibilità.
"""

from fastapi import APIRouter

# Import router modulari
from .batch_nesting_crud import router as crud_router
from .batch_nesting_workflow import router as workflow_router
from .batch_nesting_generation import router as generation_router
from .batch_nesting_results import router as results_router
from .batch_nesting_maintenance import router as maintenance_router

# Router principale
router = APIRouter()

# Inclusione router modulari
router.include_router(crud_router)
router.include_router(workflow_router)
router.include_router(generation_router)
router.include_router(results_router)
router.include_router(maintenance_router)
'''
    
    file_path = Path("backend/api/routers/batch_nesting_modular.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato router principale: {file_path}")

def main():
    """Esegue la ristrutturazione"""
    print("🚀 INIZIO RISTRUTTURAZIONE BATCH_NESTING.PY")
    print("=" * 50)
    
    try:
        # 1. Backup
        create_backup()
        
        # 2. Directory
        create_directories()
        
        # 3. Router modulari
        print("\n🔧 Creando router modulari...")
        create_crud_router()
        create_workflow_router()
        create_generation_router()
        create_results_router()
        create_maintenance_router()
        
        # 4. Servizi
        print("\n🛠️ Creando servizi...")
        create_batch_service()
        create_workflow_service()
        
        # 5. Router principale
        print("\n🎯 Creando router principale...")
        create_main_router()
        
        print("\n✅ RISTRUTTURAZIONE COMPLETATA!")
        print("📋 PROSSIMI PASSI:")
        print("1. Migrare implementazioni dai TODO nel file originale")
        print("2. Aggiornare import nel main.py")
        print("3. Testare tutti gli endpoint")
        print("4. Rimuovere file originale quando tutto funziona")
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")

if __name__ == "__main__":
    main() 