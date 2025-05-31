#!/usr/bin/env python3
"""
Test per verificare l'integrazione enhanced nesting con il frontend
"""
import requests
import json

def test_enhanced_preview():
    """Testa l'endpoint enhanced-preview"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Verifica salute del sistema
    print("🔍 1. Verifica salute sistema...")
    health = requests.get(f"{base_url}/../health")
    if health.status_code == 200:
        print("✅ Backend healthy")
    else:
        print("❌ Backend non disponibile")
        return False
    
    # 2. Ottieni ODL disponibili
    print("\n🔍 2. Verifica ODL disponibili...")
    odl_response = requests.get(f"{base_url}/nesting/auto-multi/odl-disponibili")
    if odl_response.status_code == 200:
        odl_data = odl_response.json()
        if odl_data.get('success'):
            odl_list = odl_data.get('data', [])
            print(f"✅ Trovati {len(odl_list)} ODL disponibili")
            if len(odl_list) >= 2:
                # Prendi i primi 2 ODL
                odl_ids = [odl['id'] for odl in odl_list[:2]]
                print(f"   ODL selezionati: {odl_ids}")
            else:
                print("❌ Servono almeno 2 ODL per il test")
                return False
        else:
            print("❌ Errore nel recupero ODL:", odl_data.get('error'))
            return False
    else:
        print("❌ Errore HTTP ODL:", odl_response.status_code)
        return False
    
    # 3. Ottieni autoclavi disponibili
    print("\n🔍 3. Verifica autoclavi disponibili...")
    autoclave_response = requests.get(f"{base_url}/nesting/auto-multi/autoclavi-disponibili")
    if autoclave_response.status_code == 200:
        autoclave_data = autoclave_response.json()
        if autoclave_data.get('success'):
            autoclave_list = autoclave_data.get('data', [])
            print(f"✅ Trovate {len(autoclave_list)} autoclavi disponibili")
            if len(autoclave_list) >= 1:
                autoclave_id = autoclave_list[0]['id']
                autoclave_nome = autoclave_list[0]['nome']
                print(f"   Autoclave selezionata: {autoclave_id} ({autoclave_nome})")
            else:
                print("❌ Nessuna autoclave disponibile")
                return False
        else:
            print("❌ Errore nel recupero autoclavi:", autoclave_data.get('error'))
            return False
    else:
        print("❌ Errore HTTP autoclavi:", autoclave_response.status_code)
        return False
    
    # 4. Test Enhanced Preview
    print("\n🔍 4. Test Enhanced Preview...")
    enhanced_payload = {
        "odl_ids": odl_ids,
        "autoclave_id": autoclave_id,
        "constraints": {
            "distanza_minima_tool_mm": 20,
            "padding_bordo_mm": 15,
            "margine_sicurezza_peso_percent": 10,
            "efficienza_minima_percent": 30,
            "separa_cicli_cura": True,
            "abilita_rotazioni": True
        }
    }
    
    enhanced_response = requests.post(
        f"{base_url}/nesting/enhanced-preview",
        json=enhanced_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if enhanced_response.status_code == 200:
        enhanced_data = enhanced_response.json()
        if enhanced_data.get('success'):
            data = enhanced_data.get('data', {})
            
            print("✅ Enhanced Preview SUCCESS!")
            print("   📊 Statistiche:")
            stats = data.get('statistiche', {})
            print(f"      Efficienza geometrica: {stats.get('efficienza_geometrica', 0):.1f}%")
            print(f"      Efficienza totale: {stats.get('efficienza_totale', 0):.1f}%")
            print(f"      Peso totale: {stats.get('peso_totale_kg', 0):.1f} kg")
            print(f"      Valvole: {stats.get('valvole_utilizzate', 0)}/{stats.get('valvole_totali', 0)}")
            
            print("   🎯 Layout:")
            posizioni = data.get('posizioni_tool', [])
            print(f"      Tool posizionati: {len(posizioni)}")
            for pos in posizioni:
                print(f"         ODL {pos.get('odl_id')}: ({pos.get('x')}, {pos.get('y')}) "
                      f"{pos.get('width')}×{pos.get('height')}mm piano {pos.get('piano')}")
            
            odl_inclusi = data.get('odl_inclusi', [])
            odl_esclusi = data.get('odl_esclusi', [])
            print(f"      ODL inclusi: {len(odl_inclusi)}")
            print(f"      ODL esclusi: {len(odl_esclusi)}")
            
            for escluso in odl_esclusi:
                print(f"         ❌ {escluso.get('numero_odl')}: {escluso.get('motivo')}")
            
            # Test dimensioni autoclave
            autoclave_info = data.get('autoclave', {})
            print("   🏭 Autoclave:")
            print(f"      Dimensioni: {autoclave_info.get('lunghezza')}×{autoclave_info.get('larghezza_piano')}mm")
            print(f"      Carico max: {autoclave_info.get('max_load_kg')} kg")
            print(f"      Valvole: {autoclave_info.get('num_linee_vuoto')}")
            
            # Test dimensioni effettive
            eff_dims = data.get('effective_dimensions', {})
            print("   📐 Dimensioni effettive:")
            print(f"      Area utilizzabile: {eff_dims.get('usable_width_mm')}×{eff_dims.get('usable_height_mm')}mm")
            print(f"      Margine bordo: {eff_dims.get('border_padding_mm')}mm")
            
            return True
        else:
            print("❌ Enhanced Preview FAILED:", enhanced_data.get('error'))
            return False
    else:
        print(f"❌ Errore HTTP Enhanced Preview: {enhanced_response.status_code}")
        try:
            error_data = enhanced_response.json()
            print(f"   Dettagli: {error_data}")
        except:
            print(f"   Testo errore: {enhanced_response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Test Enhanced Nesting Frontend Integration")
    print("=" * 60)
    
    success = test_enhanced_preview()
    
    if success:
        print("\n🎉 TUTTI I TEST SUPERATI!")
        print("💡 Il sistema enhanced nesting è completamente funzionante")
        print("🌐 Apri http://localhost:3000/dashboard/curing/nesting/auto-multi")
        print("   per testare la nuova visualizzazione enhanced!")
    else:
        print("\n❌ ALCUNI TEST FALLITI!")
        print("🔧 Verifica configurazione backend/frontend") 