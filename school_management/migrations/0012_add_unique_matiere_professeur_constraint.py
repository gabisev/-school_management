# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school_management', '0011_clean_duplicate_assignments'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='emploidutemps',
            unique_together={
                ('classe', 'creneau', 'annee_scolaire', 'semestre'),
                ('classe', 'matiere', 'annee_scolaire', 'semestre')
            },
        ),
    ]



