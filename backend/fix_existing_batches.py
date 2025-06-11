#!/usr/bin/env python3
"""
Fix per batch esistenti - Aggiunge campi mancanti nella configurazione JSON
"""

import json
from sqlalchemy.orm import Session
from models.db import SessionLocal
from models.batch_nesting import BatchNesting
from models.autoclave import Autoclave

def fix_existing_batches():
    """Aggiorna batch esistenti con campi mancanti"""
    db = SessionLocal()
    
    try:
        print("🔧 Fix batch esistenti - Aggiunta campi canvas")
        
        # Recupera tutti i batch
        batches = db.query(BatchNesting).all()
        print(f"📦 Trovati {len(batches)} batch da verificare")
        
        fixed_count = 0
        
        for batch in batches:
            try:
                # Controlla se la configurazione JSON ha i campi necessari
                config = batch.configurazione_json or {}
                
                if 'canvas_width' not in config or 'canvas_height' not in config:
                    print(f"\n🔧 Fix batch {batch.id[:8]}... - {batch.nome}")
                    
                    # Recupera autoclave per dimensioni
                    autoclave = db.query(Autoclave).filter(Autoclave.id == batch.autoclave_id).first()
                    
                    if autoclave:
                        # Aggiorna configurazione (usa nomi corretti campi autoclave)
                        config['canvas_width'] = autoclave.larghezza_piano or 800
                        config['canvas_height'] = autoclave.lunghezza or 600
                        
                        # Salva configurazione aggiornata
                        batch.configurazione_json = config
                        
                        print(f"   ✅ Aggiornato: canvas_width={config['canvas_width']}, canvas_height={config['canvas_height']}")
                        fixed_count += 1
                    else:
                        print(f"   ⚠️ Autoclave {batch.autoclave_id} non trovata - usando valori default")
                        config['canvas_width'] = 800
                        config['canvas_height'] = 600
                        batch.configurazione_json = config
                        fixed_count += 1
                        
                else:
                    print(f"✅ Batch {batch.id[:8]}... già OK")
                    
            except Exception as e:
                print(f"❌ Errore batch {batch.id}: {e}")
        
        # Commit tutte le modifiche
        if fixed_count > 0:
            db.commit()
            print(f"\n🎉 Fix completato!")
            print(f"   ✅ {fixed_count} batch aggiornati")
            print(f"   📦 {len(batches)} batch totali")
        else:
            print(f"\n✅ Nessun batch da aggiornare")
        
    except Exception as e:
        print(f"❌ Errore fix batch: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_existing_batches() 