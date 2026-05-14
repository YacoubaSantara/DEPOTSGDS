"""
Migration 0004 : Supprime le champ role_old (devenu inutile après 0003)
et rend le champ role (FK) non nullable.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_seed_roles_and_migrate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='role_old',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='utilisateurs',
                to='users.role',
                verbose_name='Rôle',
            ),
        ),
    ]
