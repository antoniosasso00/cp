#!/usr/bin/env python3
"""
Test per verificare l'import di status da FastAPI
"""

print("🔍 Test import status da FastAPI...")

try:
    from fastapi import status
    print(f"✅ Import status riuscito: {status}")
    print(f"📋 Tipo di status: {type(status)}")
    
    # Test specifico per HTTP_500_INTERNAL_SERVER_ERROR
    if hasattr(status, 'HTTP_500_INTERNAL_SERVER_ERROR'):
        print(f"✅ HTTP_500_INTERNAL_SERVER_ERROR disponibile: {status.HTTP_500_INTERNAL_SERVER_ERROR}")
    else:
        print("❌ HTTP_500_INTERNAL_SERVER_ERROR NON disponibile")
        
    # Mostra tutti gli attributi disponibili
    print(f"📋 Attributi status disponibili: {[attr for attr in dir(status) if not attr.startswith('_')]}")
    
except ImportError as e:
    print(f"❌ Errore import: {e}")
except Exception as e:
    print(f"❌ Errore generico: {e}")

print("\n🔍 Test import alternativo...")
try:
    from fastapi.status import HTTP_500_INTERNAL_SERVER_ERROR
    print(f"✅ Import diretto riuscito: {HTTP_500_INTERNAL_SERVER_ERROR}")
except ImportError as e:
    print(f"❌ Import diretto fallito: {e}") 