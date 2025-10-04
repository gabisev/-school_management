#!/usr/bin/env python
"""
Script pour créer des données d'emploi du temps pour les élèves
"""

import os
import sys
import django
from datetime import time, datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
django.setup()

from school_management.models import (
    Salle, Creneau, EmploiDuTemps, Classe, Matiere, Professeur
)

def create_creneaux():
    """Créer les créneaux horaires"""
    print("Création des créneaux horaires...")
    
    # Créneaux pour une journée type
    creneaux_data = [
        # Lundi
        ('LUNDI', time(8, 0), time(9, 0), 60, False),
        ('LUNDI', time(9, 0), time(10, 0), 60, True),  # Récréation
        ('LUNDI', time(10, 15), time(11, 15), 60, False),
        ('LUNDI', time(11, 15), time(12, 15), 60, False),
        ('LUNDI', time(14, 0), time(15, 0), 60, False),
        ('LUNDI', time(15, 0), time(16, 0), 60, True),  # Récréation
        ('LUNDI', time(16, 15), time(17, 15), 60, False),
        
        # Mardi
        ('MARDI', time(8, 0), time(9, 0), 60, False),
        ('MARDI', time(9, 0), time(10, 0), 60, True),
        ('MARDI', time(10, 15), time(11, 15), 60, False),
        ('MARDI', time(11, 15), time(12, 15), 60, False),
        ('MARDI', time(14, 0), time(15, 0), 60, False),
        ('MARDI', time(15, 0), time(16, 0), 60, True),
        ('MARDI', time(16, 15), time(17, 15), 60, False),
        
        # Mercredi
        ('MERCREDI', time(8, 0), time(9, 0), 60, False),
        ('MERCREDI', time(9, 0), time(10, 0), 60, True),
        ('MERCREDI', time(10, 15), time(11, 15), 60, False),
        ('MERCREDI', time(11, 15), time(12, 15), 60, False),
        
        # Jeudi
        ('JEUDI', time(8, 0), time(9, 0), 60, False),
        ('JEUDI', time(9, 0), time(10, 0), 60, True),
        ('JEUDI', time(10, 15), time(11, 15), 60, False),
        ('JEUDI', time(11, 15), time(12, 15), 60, False),
        ('JEUDI', time(14, 0), time(15, 0), 60, False),
        ('JEUDI', time(15, 0), time(16, 0), 60, True),
        ('JEUDI', time(16, 15), time(17, 15), 60, False),
        
        # Vendredi
        ('VENDREDI', time(8, 0), time(9, 0), 60, False),
        ('VENDREDI', time(9, 0), time(10, 0), 60, True),
        ('VENDREDI', time(10, 15), time(11, 15), 60, False),
        ('VENDREDI', time(11, 15), time(12, 15), 60, False),
        ('VENDREDI', time(14, 0), time(15, 0), 60, False),
        ('VENDREDI', time(15, 0), time(16, 0), 60, True),
        ('VENDREDI', time(16, 15), time(17, 15), 60, False),
    ]
    
    creneaux_created = 0
    for jour, heure_debut, heure_fin, duree, pause in creneaux_data:
        creneau, created = Creneau.objects.get_or_create(
            jour=jour,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            defaults={
                'duree_minutes': duree,
                'pause': pause
            }
        )
        if created:
            creneaux_created += 1
    
    print(f"✅ {creneaux_created} créneaux créés")
    return Creneau.objects.all()

def create_emplois_du_temps():
    """Créer des emplois du temps pour les classes"""
    print("Création des emplois du temps...")
    
    # Récupérer les données nécessaires
    classes = Classe.objects.all()
    matieres = Matiere.objects.all()
    professeurs = Professeur.objects.all()
    salles = Salle.objects.all()
    creneaux = Creneau.objects.all()
    
    if not classes.exists():
        print("❌ Aucune classe trouvée. Créez d'abord des classes.")
        return
    
    if not matieres.exists():
        print("❌ Aucune matière trouvée. Créez d'abord des matières.")
        return
    
    if not professeurs.exists():
        print("❌ Aucun professeur trouvé. Créez d'abord des professeurs.")
        return
    
    if not salles.exists():
        print("❌ Aucune salle trouvée. Créez d'abord des salles.")
        return
    
    emplois_created = 0
    
    # Créer un emploi du temps pour chaque classe
    for classe in classes:
        print(f"  Création de l'emploi du temps pour {classe.nom}...")
        
        # Matières principales pour chaque niveau
        matieres_principales = {
            '6ème': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            '5ème': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            '4ème': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            '3ème': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            '2nde': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            '1ère': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
            'Terminale': ['Mathématiques', 'Français', 'Anglais', 'Histoire-Géographie', 'Sciences', 'EPS'],
        }
        
        # Obtenir les matières pour ce niveau
        niveau_matiere = matieres_principales.get(classe.niveau, matieres_principales['6ème'])
        matieres_classe = matieres.filter(nom__in=niveau_matiere)
        
        # Créer des emplois pour chaque jour
        jours = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI']
        creneaux_par_jour = {}
        
        for jour in jours:
            creneaux_par_jour[jour] = list(creneaux.filter(jour=jour, pause=False).order_by('heure_debut'))
        
        # Distribuer les matières sur les créneaux
        matiere_index = 0
        for jour in jours:
            creneaux_jour = creneaux_par_jour[jour]
            
            for i, creneau in enumerate(creneaux_jour):
                if matieres_classe.exists():
                    matiere = matieres_classe[matiere_index % len(matieres_classe)]
                    professeur = professeurs[matiere_index % len(professeurs)]
                    salle = salles[matiere_index % len(salles)]
                    
                    emploi, created = EmploiDuTemps.objects.get_or_create(
                        classe=classe,
                        creneau=creneau,
                        defaults={
                            'matiere': matiere,
                            'professeur': professeur,
                            'salle': salle,
                            'type_cours': 'COURS',
                            'annee_scolaire': '2024-2025',
                            'semestre': 1,
                            'actif': True,
                            'commentaire': f'Cours de {matiere.nom}'
                        }
                    )
                    
                    if created:
                        emplois_created += 1
                    
                    matiere_index += 1
    
    print(f"✅ {emplois_created} emplois du temps créés")

def main():
    """Fonction principale"""
    print("🚀 Création des données d'emploi du temps pour les élèves...")
    print("=" * 60)
    
    try:
        # Créer les créneaux
        creneaux = create_creneaux()
        
        # Créer les emplois du temps
        create_emplois_du_temps()
        
        print("=" * 60)
        print("✅ Données d'emploi du temps créées avec succès !")
        print("\n📊 Résumé :")
        print(f"   - Créneaux : {Creneau.objects.count()}")
        print(f"   - Emplois du temps : {EmploiDuTemps.objects.count()}")
        print(f"   - Classes : {Classe.objects.count()}")
        print(f"   - Matières : {Matiere.objects.count()}")
        print(f"   - Professeurs : {Professeur.objects.count()}")
        print(f"   - Salles : {Salle.objects.count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()




