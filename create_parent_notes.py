#!/usr/bin/env python
"""
Script pour créer des notes pour l'enfant du parent
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from school_management.models import Parent, Eleve, Note, Evaluation

def create_parent_notes():
    """Créer des notes pour l'enfant du parent"""
    parent = Parent.objects.first()
    if not parent:
        print("Aucun parent trouvé")
        return
    
    enfant = parent.eleves.first()
    if not enfant:
        print("Aucun enfant associé au parent")
        return
    
    print(f"Création de notes pour {enfant.user.first_name} {enfant.user.last_name}")
    
    # Récupérer les évaluations de la classe de l'enfant
    evaluations = Evaluation.objects.filter(classe=enfant.classe)[:3]
    
    for eval in evaluations:
        note, created = Note.objects.get_or_create(
            eleve=enfant, 
            evaluation=eval, 
            defaults={
                'note': 15.5, 
                'commentaire': 'Bien'
            }
        )
        if created:
            print(f"Note créée: {eval.titre} - {note.note}/20")
        else:
            print(f"Note existante: {eval.titre} - {note.note}/20")

if __name__ == '__main__':
    create_parent_notes()






