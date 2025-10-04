# Generated manually

from django.db import migrations
from django.db.models import Count


def clean_duplicate_prof_principal(apps, schema_editor):
    """Supprime les assignations en double (même professeur principal pour plusieurs classes)"""
    Classe = apps.get_model('school_management', 'Classe')
    
    # Trouver les groupes avec des doublons
    duplicates = Classe.objects.values('prof_principal').annotate(
        count=Count('id')
    ).filter(count__gt=1, prof_principal__isnull=False)
    
    for duplicate in duplicates:
        prof_id = duplicate['prof_principal']
        # Récupérer toutes les classes pour ce professeur
        classes = Classe.objects.filter(prof_principal_id=prof_id).order_by('id')
        
        # Garder la première classe, retirer le professeur principal des autres
        classe_to_keep = classes.first()
        classes_to_update = classes.exclude(id=classe_to_keep.id)
        
        print(f"Conservation du professeur principal pour {classe_to_keep.nom}, retrait des autres classes")
        classes_to_update.update(prof_principal=None)


def reverse_clean_duplicate_prof_principal(apps, schema_editor):
    """Opération inverse - ne peut pas être inversée"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('school_management', '0012_add_unique_matiere_professeur_constraint'),
    ]

    operations = [
        migrations.RunPython(clean_duplicate_prof_principal, reverse_clean_duplicate_prof_principal),
    ]



