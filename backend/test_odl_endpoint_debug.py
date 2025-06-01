#!/usr/bin/env python3
"""
Test specifico per debuggare l'endpoint ODL
"""

import requests
import json
import traceback

BASE_URL = "http://localhost:8000"

def test_odl_endpoint():
    """Test dell'endpoint ODL con debug dettagliato"""
    
    print("🔍 Test endpoint ODL con debug...")
    
    try:
        # Test 1: Health check
        print("\n1️⃣ Test health check...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Database: {health_data.get('database', 'N/A')}")
            print(f"   Tabelle: {health_data.get('tables_count', 'N/A')}")
        
        # Test 2: Endpoint ODL diretto
        print("\n2️⃣ Test endpoint ODL...")
        response = requests.get(f"{BASE_URL}/api/v1/odl", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Successo! Trovati {len(data)} ODL")
            if data:
                print(f"   📋 Primo ODL: {data[0]}")
        else:
            print(f"   ❌ Errore {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📋 Dettagli errore: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   📋 Risposta raw: {response.text}")
        
        # Test 3: Endpoint con parametri
        print("\n3️⃣ Test endpoint ODL con parametri...")
        response = requests.get(f"{BASE_URL}/api/v1/odl?limit=5", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   📋 Errore con parametri: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   📋 Risposta raw: {response.text}")
        
        # Test 4: Verifica database diretto
        print("\n4️⃣ Test database diretto...")
        try:
            import sys
            sys.path.append('.')
            
            from api.database import get_db
            from models.odl import ODL
            
            db = next(get_db())
            odl_count = db.query(ODL).count()
            print(f"   📊 ODL nel database: {odl_count}")
            
            # Prova a recuperare un ODL con relazioni
            if odl_count > 0:
                from sqlalchemy.orm import joinedload
                odl = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).first()
                print(f"   📋 ODL di test: ID={odl.id}, Status={odl.status}")
                print(f"   📋 Parte: {odl.parte.descrizione_breve if odl.parte else 'None'}")
                print(f"   📋 Tool: {odl.tool.part_number_tool if odl.tool else 'None'}")
            
        except Exception as db_error:
            print(f"   ❌ Errore database: {str(db_error)}")
            traceback.print_exc()
        
    except requests.exceptions.ConnectionError:
        print("❌ Server non raggiungibile. Assicurati che sia in esecuzione.")
    except Exception as e:
        print(f"❌ Errore imprevisto: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_odl_endpoint() 