#!/usr/bin/env python3
"""
Server temporaneo per l'endpoint ODL disponibili.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models.db import SessionLocal
from models import ODL, Tool
import uvicorn
from typing import Optional

app = FastAPI(title="Server Temporaneo ODL")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/nesting/auto-multi/odl-disponibili")
async def get_odl_disponibili(
    db: Session = Depends(get_db),
    ciclo_cura_id: Optional[int] = None,
    priorita: Optional[str] = None
):
    """
    Recupera tutti gli ODL con stato 'Attesa Cura' disponibili per il nesting.
    """
    try:
        # Query diretta
        all_odl = db.query(ODL).filter(ODL.status == "Attesa Cura").all()
        
        odl_data = []
        for odl in all_odl:
            # Controlla se ha un tool e se è disponibile
            if not odl.tool or not odl.tool.disponibile:
                continue
            
            tool = odl.tool
            
            # Determina la priorità
            priorita_str = "Alta" if odl.priorita >= 3 else "Media" if odl.priorita >= 2 else "Bassa"
            
            # Applica filtro priorità se specificato
            if priorita and priorita != "all" and priorita_str != priorita:
                continue
                
            # Ciclo di cura
            try:
                if odl.parte and odl.parte.ciclo_cura:
                    ciclo_cura_info = {
                        "id": odl.parte.ciclo_cura.id,
                        "nome": odl.parte.ciclo_cura.nome
                    }
                    
                    # Applica filtro ciclo se specificato
                    if ciclo_cura_id and ciclo_cura_info["id"] != ciclo_cura_id:
                        continue
                else:
                    ciclo_cura_info = {"id": 1, "nome": "Standard"}
            except:
                ciclo_cura_info = {"id": 1, "nome": "Standard"}
            
            # Calcola area stimata
            area_stimata = 0
            if tool.lunghezza_piano and tool.larghezza_piano:
                area_stimata = (tool.lunghezza_piano * tool.larghezza_piano) / 100
            
            odl_item = {
                "id": odl.id,
                "numero_odl": f"ODL-{odl.id:06d}",
                "parte_nome": odl.parte.descrizione_breve if odl.parte else "N/A",
                "tool_nome": tool.part_number_tool,
                "tool_dimensioni": {
                    "lunghezza": tool.lunghezza_piano or 0,
                    "larghezza": tool.larghezza_piano or 0
                },
                "peso_kg": tool.peso or 0.0,
                "area_stimata": area_stimata,
                "ciclo_cura": ciclo_cura_info,
                "priorita": priorita_str,
                "data_creazione": odl.created_at.isoformat() if odl.created_at else None
            }
            
            odl_data.append(odl_item)
        
        return {
            "success": True,
            "data": odl_data,
            "total": len(odl_data)
        }
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "total": 0
        }

@app.get("/api/v1/nesting/auto-multi/autoclavi-disponibili")
async def get_autoclavi_disponibili(db: Session = Depends(get_db)):
    """
    Recupera autoclavi disponibili.
    """
    try:
        from models import Autoclave
        autoclavi = db.query(Autoclave).filter(
            Autoclave.stato == "DISPONIBILE"
        ).all()
        
        autoclavi_data = []
        for autoclave in autoclavi:
            autoclavi_data.append({
                "id": autoclave.id,
                "nome": autoclave.nome,
                "dimensioni": {
                    "lunghezza": autoclave.lunghezza,
                    "larghezza": autoclave.larghezza_piano
                },
                "capacita_peso_kg": autoclave.max_load_kg or 1000.0,
                "superficie_piano_1": autoclave.area_piano,
                "superficie_piano_2": autoclave.area_piano / 2 if autoclave.use_secondary_plane else 0,
                "stato": autoclave.stato.value
            })
        
        return {
            "success": True,
            "data": autoclavi_data,
            "total": len(autoclavi_data)
        }
        
    except Exception as e:
        print(f"❌ Errore autoclavi: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": [],
            "total": 0
        }

if __name__ == "__main__":
    print("🚀 Avvio server temporaneo su porta 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 