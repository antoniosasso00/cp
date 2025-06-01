#!/usr/bin/env python3
import requests
import json

def test_server():
    try:
        print("Testing server health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Database tables: {data.get('database', {}).get('tables_count', 'N/A')}")
            print(f"Routes count: {data.get('api', {}).get('routes_count', 'N/A')}")
        
        print("\nTesting ODL endpoint...")
        response = requests.get("http://localhost:8000/api/v1/odl?limit=1", timeout=5)
        print(f"ODL endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"ODL count: {len(data)}")
        else:
            print(f"ODL error: {response.text}")
            
        print("\nTesting nesting data endpoint...")
        response = requests.get("http://localhost:8000/api/v1/nesting/data", timeout=5)
        print(f"Nesting data status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Nesting data received: {data.get('status', 'N/A')}")
        else:
            print(f"Nesting data error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_server() 