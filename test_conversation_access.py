#!/usr/bin/env python
"""
Test d'accès à la création de conversation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_conversation_access():
    """Test d'accès à la création de conversation"""
    print("🧪 Test d'accès à la création de conversation...")
    
    client = Client()
    
    # Test pour un parent
    print("\n👨‍👩‍👧‍👦 Test pour un parent:")
    parent_user = User.objects.filter(parent__isnull=False).first()
    if parent_user:
        print(f"   Parent: {parent_user.get_full_name()}")
        
        # Se connecter
        client.force_login(parent_user)
        
        # Accéder à la page de création
        response = client.get('/messagerie/conversations/nouvelle/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Accès autorisé à la création de conversation")
            
            # Vérifier que le formulaire est présent
            if 'form' in response.context:
                form = response.context['form']
                print(f"   Formulaire présent: {form is not None}")
                print(f"   Champs disponibles: {list(form.fields.keys())}")
                
                # Vérifier les classes disponibles
                classes_queryset = form.fields['classe'].queryset
                print(f"   Classes disponibles: {list(classes_queryset.values_list('nom', flat=True))}")
            else:
                print("   ❌ Formulaire non présent dans le contexte")
        else:
            print(f"   ❌ Accès refusé: {response.status_code}")
    
    # Test pour un élève
    print("\n👨‍🎓 Test pour un élève:")
    eleve_user = User.objects.filter(eleve__isnull=False).first()
    if eleve_user:
        print(f"   Élève: {eleve_user.get_full_name()}")
        
        # Se connecter
        client.force_login(eleve_user)
        
        # Accéder à la page de création
        response = client.get('/messagerie/conversations/nouvelle/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Accès autorisé à la création de conversation")
            
            # Vérifier que le formulaire est présent
            if 'form' in response.context:
                form = response.context['form']
                print(f"   Formulaire présent: {form is not None}")
                print(f"   Champs disponibles: {list(form.fields.keys())}")
                
                # Vérifier les classes disponibles
                classes_queryset = form.fields['classe'].queryset
                print(f"   Classes disponibles: {list(classes_queryset.values_list('nom', flat=True))}")
            else:
                print("   ❌ Formulaire non présent dans le contexte")
        else:
            print(f"   ❌ Accès refusé: {response.status_code}")

if __name__ == "__main__":
    test_conversation_access()




