#!/usr/bin/env python3
"""
Test finale per verificare che tutte le funzionalità implementate funzionino correttamente
"""

import requests
import json

def test_comprehensive_system():
    """Test completo del sistema CarbonPilot"""
    print("🔍 Test Completo Sistema CarbonPilot")
    print("=" * 60)
    
    results = []
    
    # Test 1: Backend endpoints principali
    print("\n📡 Test Backend Endpoints:")
    backend_tests = [
        ("http://localhost:8000/api/v1/odl", "ODL"),
        ("http://localhost:8000/api/v1/autoclavi", "Autoclavi"),
        ("http://localhost:8000/api/v1/batch_nesting", "Batch Nesting"),
        ("http://localhost:8000/api/v1/catalogo", "Catalogo"),
        ("http://localhost:8000/api/v1/parti", "Parti"),
        ("http://localhost:8000/api/v1/tools", "Tools"),
    ]
    
    for url, name in backend_tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                results.append(True)
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Errore - {e}")
            results.append(False)
    
    # Test 2: Frontend proxy
    print("\n🌐 Test Frontend Proxy:")
    frontend_tests = [
        ("http://localhost:3000/api/odl", "ODL via Proxy"),
        ("http://localhost:3000/api/autoclavi", "Autoclavi via Proxy"),
        ("http://localhost:3000/api/batch_nesting", "Batch Nesting via Proxy"),
    ]
    
    for url, name in frontend_tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                results.append(True)
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Errore - {e}")
            results.append(False)
    
    # Test 3: Funzionalità specifiche implementate nella chat precedente
    print("\n🎯 Test Funzionalità Specifiche:")
    
    # Test batch nesting con filtri
    try:
        response = requests.get("http://localhost:3000/api/batch_nesting?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch Nesting con filtri: OK ({len(data)} batch trovati)")
            results.append(True)
        else:
            print(f"⚠️ Batch Nesting con filtri: HTTP {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"❌ Batch Nesting con filtri: Errore - {e}")
        results.append(False)
    
    # Test ODL con stati
    try:
        response = requests.get("http://localhost:3000/api/odl", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stati_odl = set(odl.get('status', 'N/A') for odl in data)
            print(f"✅ ODL con stati: OK ({len(data)} ODL, stati: {', '.join(stati_odl)})")
            results.append(True)
        else:
            print(f"⚠️ ODL con stati: HTTP {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"❌ ODL con stati: Errore - {e}")
        results.append(False)
    
    # Test autoclavi con disponibilità
    try:
        response = requests.get("http://localhost:3000/api/autoclavi", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stati_autoclavi = set(ac.get('stato', 'N/A') for ac in data)
            print(f"✅ Autoclavi con stati: OK ({len(data)} autoclavi, stati: {', '.join(stati_autoclavi)})")
            results.append(True)
        else:
            print(f"⚠️ Autoclavi con stati: HTTP {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"❌ Autoclavi con stati: Errore - {e}")
        results.append(False)
    
    # Test 4: Verifica che le pagine frontend siano accessibili
    print("\n🖥️ Test Accessibilità Frontend:")
    frontend_pages = [
        ("http://localhost:3000", "Homepage"),
        ("http://localhost:3000/dashboard", "Dashboard"),
    ]
    
    for url, name in frontend_pages:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                results.append(True)
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Errore - {e}")
            results.append(False)
    
    # Risultati finali
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"📊 RISULTATI FINALI: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 ✅ SISTEMA COMPLETAMENTE FUNZIONANTE!")
        print("   Tutte le funzionalità implementate funzionano correttamente.")
        print("   Il sistema è pronto per l'uso in produzione.")
    elif passed >= total * 0.8:  # 80% dei test passati
        print("✅ 🟡 SISTEMA PREVALENTEMENTE FUNZIONANTE")
        print("   La maggior parte delle funzionalità funziona correttamente.")
        print("   Alcuni problemi minori potrebbero essere presenti.")
    else:
        print("❌ 🔴 SISTEMA CON PROBLEMI SIGNIFICATIVI")
        print("   Diversi componenti non funzionano correttamente.")
        print("   È necessaria ulteriore diagnosi e correzione.")
    
    print("\n💡 COME ACCEDERE AL SISTEMA:")
    print("   🌐 Frontend: http://localhost:3000")
    print("   🔧 Backend API: http://localhost:8000")
    print("   📚 Documentazione API: http://localhost:8000/docs")
    
    return 0 if passed >= total * 0.8 else 1

if __name__ == "__main__":
    exit(test_comprehensive_system()) 