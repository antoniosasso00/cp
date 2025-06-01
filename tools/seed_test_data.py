#!/usr/bin/env python3
"""
Script di seed per inserire dati di test per StandardTime.

Inserisce tempi standard fittizi per il part number TEST-E2E-001
nelle fasi di Laminazione e Cura.
"""

import sys
import os
import sqlite3
from datetime import datetime

def create_test_data():
    """
    Crea dati di test per StandardTime usando SQLite direttamente.
    """
    # Usa il percorso assoluto del database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'carbonpilot.db')
    db_path = os.path.abspath(db_path)
    
    print(f"📍 Usando database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica che esista il part number TEST-E2E-001 nel catalogo
        cursor.execute("SELECT part_number FROM cataloghi WHERE part_number = ?", ("TEST-E2E-001",))
        catalogo_esistente = cursor.fetchone()
        
        if not catalogo_esistente:
            print("⚠️ Part number TEST-E2E-001 non trovato nel catalogo.")
            print("Creo prima il record nel catalogo...")
            
            # Crea il record nel catalogo se non esiste
            cursor.execute("""
                INSERT INTO cataloghi (part_number, descrizione, categoria, sotto_categoria, attivo, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "TEST-E2E-001",
                "Part number di test per End-to-End testing",
                "Test",
                "E2E Testing",
                1,  # True in SQLite
                "Creato automaticamente per test dei tempi standard",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            print("✅ Catalogo TEST-E2E-001 creato con successo!")
        
        # Verifica se esistono già tempi standard per questo part number
        cursor.execute("SELECT id FROM standard_times WHERE part_number = ?", ("TEST-E2E-001",))
        tempi_esistenti = cursor.fetchall()
        
        if tempi_esistenti:
            print(f"⚠️ Trovati {len(tempi_esistenti)} tempi standard esistenti per TEST-E2E-001")
            print("Li rimuovo per reinserire dati puliti...")
            cursor.execute("DELETE FROM standard_times WHERE part_number = ?", ("TEST-E2E-001",))
        
        # Inserisci i tempi standard di test
        tempi_test = [
            ("TEST-E2E-001", "Laminazione", 45.0, "Tempo standard per fase di laminazione - dato di test"),
            ("TEST-E2E-001", "Cura", 120.0, "Tempo standard per fase di cura - dato di test")
        ]
        
        for part_number, phase, minutes, note in tempi_test:
            cursor.execute("""
                INSERT INTO standard_times (part_number, phase, minutes, note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                part_number,
                phase,
                minutes,
                note,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        # Commit delle modifiche
        conn.commit()
        
        print("🎯 Dati di seed inseriti con successo!")
        print(f"✅ Inseriti {len(tempi_test)} tempi standard per TEST-E2E-001:")
        for part_number, phase, minutes, note in tempi_test:
            print(f"   - {phase}: {minutes} minuti")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'inserimento dei dati: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🚀 Avvio script di seed per StandardTime...")
    print("=" * 50)
    
    success = create_test_data()
    
    print("=" * 50)
    if success:
        print("✅ Script completato con successo!")
    else:
        print("❌ Script completato con errori!")
        sys.exit(1)

if __name__ == "__main__":
    main() 