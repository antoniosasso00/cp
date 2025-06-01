#!/usr/bin/env python3
import requests
import json

def test_admin_functions():
    """Testa tutte le funzioni admin del database"""
    print("🔧 TEST FUNZIONI ADMIN DATABASE")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1/admin"
    
    # 1. Test database status
    print("\n📊 1. TEST DATABASE STATUS")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/database/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Total Tables: {data.get('total_tables', 'N/A')}")
            print(f"   Critical Tables: {data.get('critical_tables_status', {})}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # 2. Test database info
    print("\n📋 2. TEST DATABASE INFO")
    print("-" * 25)
    try:
        response = requests.get(f"{base_url}/database/info", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database Type: {data.get('database_type', 'N/A')}")
            print(f"   Total Tables: {data.get('total_tables', 'N/A')}")
            print(f"   Total Records: {data.get('total_records', 'N/A')}")
            print("   Tables:")
            for table in data.get('tables', [])[:5]:  # Mostra prime 5 tabelle
                print(f"     - {table['name']}: {table['records']} records")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # 3. Test export structure
    print("\n🏗️ 3. TEST EXPORT STRUCTURE")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/database/export-structure", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Structure Export: {data.get('database_type', 'N/A')}")
            print(f"   Total Tables: {data.get('total_tables', 'N/A')}")
            print("   Sample Tables:")
            for table_name, table_info in list(data.get('tables', {}).items())[:3]:
                print(f"     - {table_name}: {len(table_info.get('columns', []))} columns, {table_info.get('record_count', 0)} records")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # 4. Test backup (download)
    print("\n💾 4. TEST BACKUP DOWNLOAD")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/backup", timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Backup Downloaded: {len(response.content)} bytes")
            # Verifica che sia JSON valido
            try:
                backup_data = response.json()
                print(f"   Tables in backup: {len(backup_data.get('tables', {}))}")
                print(f"   Export timestamp: {backup_data.get('export_timestamp', 'N/A')}")
            except:
                print("   ⚠️ Response is not JSON (might be file download)")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print(f"\n✅ Test funzioni admin completato!")

if __name__ == "__main__":
    test_admin_functions() 