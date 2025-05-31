#!/usr/bin/env python3
"""
Script per avviare il server FastAPI e testare le API BatchNesting.
"""

import subprocess
import time
import sys
import requests
from pathlib import Path

def start_server():
    """Avvia il server FastAPI in background"""
    try:
        print("🚀 Avvio del server FastAPI...")
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=Path(__file__).parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Attendi che il server si avvii
        print("⏳ Attendo che il server si avvii...")
        for i in range(30):  # Attendi fino a 30 secondi
            try:
                response = requests.get("http://localhost:8000/docs", timeout=2)
                if response.status_code == 200:
                    print("✅ Server avviato correttamente!")
                    return process
            except:
                pass
            time.sleep(1)
            print(f"   Tentativo {i+1}/30...")
        
        print("❌ Timeout nell'avvio del server")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Errore nell'avvio del server: {e}")
        return None

def test_apis():
    """Testa le API BatchNesting"""
    try:
        # Esegui il test delle API
        result = subprocess.run(
            [sys.executable, "test_batch_nesting_api.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout nel test delle API")
        return False
    except Exception as e:
        print(f"❌ Errore nel test delle API: {e}")
        return False

def main():
    """Funzione principale"""
    print("🎯 Test completo del modello BatchNesting")
    print("=" * 60)
    
    # Avvia il server
    server_process = start_server()
    
    if server_process is None:
        print("💥 Impossibile avviare il server")
        return False
    
    try:
        # Testa le API
        success = test_apis()
        
        if success:
            print("\n🎉 SUCCESSO! Tutte le API BatchNesting funzionano correttamente!")
            print("\n📋 Riepilogo funzionalità implementate:")
            print("✅ Modello SQLAlchemy BatchNesting creato")
            print("✅ Tabella database creata")
            print("✅ Schemi Pydantic per validazione")
            print("✅ Router FastAPI con operazioni CRUD")
            print("✅ API integrate nel server principale")
            print("✅ Parametri nesting salvabili nel database")
            print("✅ Configurazione layout salvabile")
            print("✅ Documentazione API in Swagger")
            
            print(f"\n🌐 Accedi a Swagger: http://localhost:8000/docs")
            print("📚 Le API BatchNesting sono disponibili sotto il tag 'Batch Nesting'")
            
            return True
        else:
            print("\n💥 Alcuni test sono falliti")
            return False
            
    finally:
        # Termina il server
        print("\n🛑 Terminazione del server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✅ Server terminato correttamente")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("⚠️ Server terminato forzatamente")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 