#!/usr/bin/env python3

import sys
sys.path.append('.')
from api.database import SessionLocal
from models import ODL, Autoclave

def analyze_real_data():
    """Analizza i dati reali del database"""
    db = SessionLocal()
    
    print('=== ANALISI DATI DINAMICI ===')
    
    # Analizza autoclavi
    autoclavi = db.query(Autoclave).all()
    print(f'Autoclavi totali: {len(autoclavi)}')
    autoclavi_2l = []
    
    for a in autoclavi:
        print(f'  {a.id}: {a.nome} - cavalletti: {a.usa_cavalletti}')
        if a.usa_cavalletti:
            autoclavi_2l.append(a.id)
    
    print(f'Autoclavi con cavalletti: {autoclavi_2l}')
    
    # Analizza ODL
    odls = db.query(ODL).filter(ODL.status == 'Attesa Cura').all()
    print(f'ODL in Attesa Cura: {len(odls)}')
    
    if odls:
        print(f'ODL IDs disponibili: {[o.id for o in odls[:10]]}')
        
        # Crea payload dinamico per test
        if autoclavi_2l and len(odls) >= 2:
            payload = {
                "autoclavi_2l": autoclavi_2l,
                "odl_ids": [o.id for o in odls[:5]],  # Primi 5 ODL
                "parametri": {
                    "padding_mm": 5,
                    "min_distance_mm": 10
                },
                "use_cavalletti": True,
                "prefer_base_level": True
            }
            
            print(f'\nPayload dinamico generato:')
            import json
            print(json.dumps(payload, indent=2))
            return payload
        else:
            print('⚠️ Dati insufficienti per test 2L')
            return None
    
    db.close()

if __name__ == "__main__":
    analyze_real_data() 