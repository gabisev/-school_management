#!/usr/bin/env python
"""
Vérification simple du serveur
"""
import requests

def check_server():
    """Vérifier que le serveur fonctionne"""
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"✅ Serveur accessible - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Serveur non accessible: {e}")
        return False

if __name__ == "__main__":
    check_server()




