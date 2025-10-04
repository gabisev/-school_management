# Generated manually

from django.db import migrations
from django.db.models import Count


def clean_duplicate_assignments(apps, schema_editor):
    """Supprime les assignations en double (même matière, même classe, même année/semestre)"""
    EmploiDuTemps = apps.get_model('school_management', 'EmploiDuTemps')
    
    # Trouver les groupes avec des doublons
    duplicates = EmploiDuTemps.objects.values(
        'classe', 'matiere', 'annee_scolaire', 'semestre'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for duplicate in duplicates:
        # Récupérer tous les emplois du temps pour ce groupe
        emplois = EmploiDuTemps.objects.filter(
            classe_id=duplicate['classe'],
            matiere_id=duplicate['matiere'],
            annee_scolaire=duplicate['annee_scolaire'],
            semestre=duplicate['semestre']
        ).order_by('date_creation')
        
        # Garder le premier, supprimer les autres
        emplois_to_keep = emplois.first()
        emplois_to_delete = emplois.exclude(id=emplois_to_keep.id)
        
        print(f"Suppression de {emplois_to_delete.count()} doublons pour {emplois_to_keep.classe} - {emplois_to_keep.matiere}")
        emplois_to_delete.delete()


def reverse_clean_duplicate_assignments(apps, schema_editor):
    """Opération inverse - ne peut pas être inversée"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('school_management', '0010_conversation_createur'),
    ]

    operations = [
        migrations.RunPython(clean_duplicate_assignments, reverse_clean_duplicate_assignments),
    ]



