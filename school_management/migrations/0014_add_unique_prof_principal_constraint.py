# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_management', '0013_clean_duplicate_prof_principal'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='classe',
            constraint=models.UniqueConstraint(
                condition=models.Q(('prof_principal__isnull', False)),
                fields=('prof_principal',),
                name='unique_prof_principal_per_classe'
            ),
        ),
    ]



