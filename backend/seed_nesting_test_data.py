"""
Script per popolare il database con dati di test per il nesting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models.db import SessionLocal, engine
from models.catalogo import Catalogo
from models.parte import Parte
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.tool import Tool
import random

def create_test_data():
    """Crea dati di test per il nesting"""
    db = SessionLocal()
    
    try:
        # Crea alcuni cataloghi con dimensioni realistiche
        cataloghi_data = [
            {
                "part_number": "CPX-001",
                "descrizione": "Pannello anteriore composito",
                "categoria": "Pannelli",
                "sotto_categoria": "Esterni",
                "lunghezza": 500.0,  # mm
                "larghezza": 300.0,  # mm
                "altezza": 5.0,      # mm
                "attivo": True
            },
            {
                "part_number": "CPX-002", 
                "descrizione": "Supporto strutturale",
                "categoria": "Strutture",
                "sotto_categoria": "Supporti",
                "lunghezza": 200.0,
                "larghezza": 150.0,
                "altezza": 10.0,
                "attivo": True
            },
            {
                "part_number": "CPX-003",
                "descrizione": "Copertura laterale",
                "categoria": "Pannelli", 
                "sotto_categoria": "Laterali",
                "lunghezza": 400.0,
                "larghezza": 250.0,
                "altezza": 3.0,
                "attivo": True
            },
            {
                "part_number": "CPX-004",
                "descrizione": "Rinforzo angolare",
                "categoria": "Strutture",
                "sotto_categoria": "Rinforzi",
                "lunghezza": 100.0,
                "larghezza": 100.0,
                "altezza": 8.0,
                "attivo": True
            },
            {
                "part_number": "CPX-005",
                "descrizione": "Pannello grande",
                "categoria": "Pannelli",
                "sotto_categoria": "Grandi",
                "lunghezza": 800.0,
                "larghezza": 600.0,
                "altezza": 4.0,
                "attivo": True
            }
        ]
        
        # Crea i cataloghi
        for cat_data in cataloghi_data:
            existing = db.query(Catalogo).filter(Catalogo.part_number == cat_data["part_number"]).first()
            if not existing:
                catalogo = Catalogo(**cat_data)
                db.add(catalogo)
        
        db.commit()
        
        # Crea alcuni tool se non esistono
        tool_data = [
            {"part_number_tool": "TOOL-001", "descrizione": "Stampo principale", "lunghezza_piano": 600.0, "larghezza_piano": 400.0},
            {"part_number_tool": "TOOL-002", "descrizione": "Stampo secondario", "lunghezza_piano": 500.0, "larghezza_piano": 300.0},
            {"part_number_tool": "TOOL-003", "descrizione": "Stampo piccolo", "lunghezza_piano": 300.0, "larghezza_piano": 200.0}
        ]
        
        for tool_info in tool_data:
            existing = db.query(Tool).filter(Tool.part_number_tool == tool_info["part_number_tool"]).first()
            if not existing:
                tool = Tool(**tool_info)
                db.add(tool)
        
        db.commit()
        
        # Crea alcune parti
        parti_data = [
            {
                "part_number": "CPX-001",
                "descrizione_breve": "Pannello anteriore",
                "num_valvole_richieste": 2
            },
            {
                "part_number": "CPX-002",
                "descrizione_breve": "Supporto strutturale",
                "num_valvole_richieste": 1
            },
            {
                "part_number": "CPX-003",
                "descrizione_breve": "Copertura laterale",
                "num_valvole_richieste": 2
            },
            {
                "part_number": "CPX-004",
                "descrizione_breve": "Rinforzo angolare",
                "num_valvole_richieste": 1
            },
            {
                "part_number": "CPX-005",
                "descrizione_breve": "Pannello grande",
                "num_valvole_richieste": 4
            }
        ]
        
        for parte_data in parti_data:
            existing = db.query(Parte).filter(Parte.part_number == parte_data["part_number"]).first()
            if not existing:
                parte = Parte(**parte_data)
                db.add(parte)
        
        db.commit()
        
        # Crea alcune autoclavi se non esistono
        autoclavi_data = [
            {
                "nome": "Autoclave Alpha",
                "codice": "AUT-001",
                "lunghezza": 1200.0,  # mm
                "larghezza_piano": 800.0,  # mm
                "num_linee_vuoto": 8,
                "temperatura_max": 180.0,
                "pressione_max": 6.0,
                "stato": StatoAutoclaveEnum.DISPONIBILE
            },
            {
                "nome": "Autoclave Beta",
                "codice": "AUT-002", 
                "lunghezza": 1000.0,
                "larghezza_piano": 600.0,
                "num_linee_vuoto": 6,
                "temperatura_max": 160.0,
                "pressione_max": 5.0,
                "stato": StatoAutoclaveEnum.DISPONIBILE
            },
            {
                "nome": "Autoclave Gamma",
                "codice": "AUT-003",
                "lunghezza": 1500.0,
                "larghezza_piano": 1000.0,
                "num_linee_vuoto": 12,
                "temperatura_max": 200.0,
                "pressione_max": 8.0,
                "stato": StatoAutoclaveEnum.DISPONIBILE
            }
        ]
        
        for aut_data in autoclavi_data:
            existing = db.query(Autoclave).filter(Autoclave.codice == aut_data["codice"]).first()
            if not existing:
                autoclave = Autoclave(**aut_data)
                db.add(autoclave)
        
        db.commit()
        
        # Crea alcuni ODL in stato "Attesa Cura"
        parti = db.query(Parte).all()
        tools = db.query(Tool).all()
        
        if parti and tools:
            for i in range(10):  # Crea 10 ODL di test
                parte = random.choice(parti)
                tool = random.choice(tools)
                
                odl = ODL(
                    parte_id=parte.id,
                    tool_id=tool.id,
                    priorita=random.randint(1, 5),
                    status="Attesa Cura",
                    note=f"ODL di test #{i+1} per nesting"
                )
                db.add(odl)
        
        db.commit()
        print("✅ Dati di test per il nesting creati con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dei dati di test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 