#!/usr/bin/env python3
"""
TEST VERIFICAZIONE FIX AUTOCLAVE ENDPOINT
Verifica che l'API delle autoclavi restituisca peso_max_per_cavalletto_kg correttamente
"""

import requests
import json

def test_autoclave_endpoint():
    """Testa l'endpoint delle autoclavi"""
    
    print("🔧 TEST VERIFICA FIX ENDPOINT AUTOCLAVI")
    print("=" * 50)
    
    try:
        # Test endpoint autoclavi
        print("\n🔍 Test endpoint /api/autoclavi...")
        
        response = requests.get("http://localhost:8000/api/autoclavi", timeout=10)
        
        if response.status_code == 200:
            autoclavi = response.json()
            print(f"✅ Endpoint OK: {len(autoclavi)} autoclavi trovate")
            
            # Verifica autoclavi 2L
            autoclavi_2l = [a for a in autoclavi if a.get('usa_cavalletti', False)]
            print(f"\n📋 AUTOCLAVI 2L: {len(autoclavi_2l)}")
            print("-" * 40)
            
            for autoclave in autoclavi_2l:
                peso_kg = autoclave.get('peso_max_per_cavalletto_kg', 0)
                max_cavalletti = autoclave.get('max_cavalletti', 0)
                
                print(f"\n🔧 {autoclave['nome']}:")
                print(f"  ⚖️  peso_max_per_cavalletto_kg: {peso_kg}kg")
                print(f"  📏 max_cavalletti: {max_cavalletti}")
                
                if peso_kg and max_cavalletti:
                    capacita_l1 = peso_kg * max_cavalletti
                    print(f"  📊 Capacità totale L1: {capacita_l1}kg")
                    
                    if peso_kg == 250.0:
                        print(f"  ✅ PESO OK: Correttamente configurato a 250kg")
                    else:
                        print(f"  ❌ PESO ERRATO: Dovrebbe essere 250kg")
                else:
                    print(f"  ❌ CAMPO MANCANTE: peso_max_per_cavalletto_kg non restituito")
            
            # Controllo finale
            all_correct = all(
                a.get('peso_max_per_cavalletto_kg') == 250.0 
                for a in autoclavi_2l
            )
            
            if all_correct:
                print(f"\n🎉 FIX COMPLETATO CON SUCCESSO!")
                print("✅ Tutti i pesi per cavalletto sono correttamente a 250kg")
                return True
            else:
                print(f"\n❌ FIX NON COMPLETO")
                print("❌ Alcuni valori peso_max_per_cavalletto_kg non sono corretti")
                return False
                
        else:
            print(f"❌ Errore endpoint: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend non raggiungibile. Assicurati che sia avviato su :8000")
        return False
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        return False

if __name__ == "__main__":
    success = test_autoclave_endpoint()
    
    if success:
        print("\n✅ ENDPOINT AUTOCLAVI COMPLETAMENTE FUNZIONANTE")
        print("🚀 Ora puoi procedere con il test 2L completo!")
    else:
        print("\n❌ PROBLEMI CON ENDPOINT AUTOCLAVI")
        print("🔧 Verifica che il backend sia avviato e gli schemi siano corretti")
    
    exit(0 if success else 1) 