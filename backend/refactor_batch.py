#!/usr/bin/env python3
"""
Script per ristrutturare batch_nesting.py in moduli separati
"""

import os
import shutil
from pathlib import Path

def create_backup():
    """Crea backup del file originale"""
    source = Path("api/routers/batch_nesting.py")
    backup = Path("api/routers/batch_nesting_backup.py")
    shutil.copy2(source, backup)
    print(f"✅ Backup creato: {backup}")

def create_directories():
    """Crea strutture directory"""
    dirs = [
        "services/batch",
        "schemas/batch", 
        "utils/batch"
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

from ..database import get_db
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

# Endpoint CRUD da migrare dal file originale
'''
    
    file_path = Path("api/routers/batch_nesting_crud.py")
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Creato: {file_path}")

def main():
    """Esegue la ristrutturazione"""
    print("🚀 INIZIO RISTRUTTURAZIONE BATCH_NESTING.PY")
    print("=" * 50)
    
    try:
        # 1. Backup
        create_backup()
        
        # 2. Directory
        create_directories()
        
        # 3. Router CRUD
        create_crud_router()
        
        print("\n✅ RISTRUTTURAZIONE BASE COMPLETATA!")
        
    except Exception as e:
        print(f"❌ ERRORE: {e}")

if __name__ == "__main__":
    main() 