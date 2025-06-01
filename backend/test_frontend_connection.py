#!/usr/bin/env python3
"""
Script per testare la connessione frontend-backend e identificare problemi specifici
"""
import requests
import json
import time

def test_frontend_backend_connection():
    """Testa la connessione tra frontend e backend"""
    print("🔍 TEST CONNESSIONE FRONTEND-BACKEND")
    print("=" * 50)
    
    # Test 1: Backend diretto
    print("\n1. 📡 TEST BACKEND DIRETTO")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:8000/api/v1/nesting/data", timeout=5)
        print(f"✅ Backend API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ODL in attesa: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"   Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
    except Exception as e:
        print(f"❌ Backend Error: {e}")
    
    # Test 2: Frontend homepage
    print("\n2. 🌐 TEST FRONTEND HOMEPAGE")
    print("-" * 30)
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"✅ Frontend Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content length: {len(response.content)} bytes")
        else:
            print(f"   Response: {response.text[:200]}...")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend Connection Error: Non posso connettermi al frontend")
    except requests.exceptions.Timeout:
        print("❌ Frontend Timeout: Il frontend non risponde entro 10 secondi")
    except Exception as e:
        print(f"❌ Frontend Error: {e}")
    
    # Test 3: Proxy API tramite frontend
    print("\n3. 🔄 TEST PROXY API")
    print("-" * 25)
    try:
        response = requests.get("http://localhost:3000/api/nesting/data", timeout=10)
        print(f"✅ Proxy API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Proxy funzionante - ODL: {len(data.get('odl_in_attesa_cura', []))}")
        else:
            print(f"   Error response: {response.text[:200]}...")
    except requests.exceptions.ConnectionError:
        print("❌ Proxy Connection Error: Il proxy non è accessibile")
    except requests.exceptions.Timeout:
        print("❌ Proxy Timeout: Il proxy non risponde entro 10 secondi")
    except Exception as e:
        print(f"❌ Proxy Error: {e}")
    
    # Test 4: Verifica porte
    print("\n4. 🔌 TEST PORTE DI SISTEMA")
    print("-" * 30)
    
    # Test porta 8000 (backend)
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        print(f"✅ Porta 8000 (Backend): ATTIVA - {response.status_code}")
    except:
        print("❌ Porta 8000 (Backend): NON ACCESSIBILE")
    
    # Test porta 3000 (frontend)
    try:
        response = requests.get("http://localhost:3000", timeout=3)
        print(f"✅ Porta 3000 (Frontend): ATTIVA - {response.status_code}")
    except:
        print("❌ Porta 3000 (Frontend): NON ACCESSIBILE")
    
    print("\n" + "=" * 50)
    print("📋 RIASSUNTO DIAGNOSI:")
    print("-" * 20)
    print("1. Se Backend OK ma Frontend/Proxy NON OK:")
    print("   → Il frontend non è in esecuzione o non risponde")
    print("   → Soluzione: Riavviare frontend con 'npm run dev'")
    print("")
    print("2. Se Backend OK e Frontend OK ma Proxy NON OK:")
    print("   → Problema di configurazione proxy")
    print("   → Verificare next.config.js")
    print("")
    print("3. Se tutto OK ma pagina nesting non funziona:")
    print("   → Problema specifico del componente React")
    print("   → Verificare console browser per errori JS")

if __name__ == "__main__":
    test_frontend_backend_connection() 