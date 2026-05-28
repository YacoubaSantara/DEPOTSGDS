"""
Migration 0007 — Ajout du champ django_group sur Role.

Ce champ crée un lien OneToOne entre chaque rôle SGDS (Role)
et un groupe Django natif (auth.Group). La synchronisation
automatique est ensuite gérée par des signaux dans signals.py.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_remove_lecteur_role'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # 1. Ajouter le champ (nullable au départ pour ne pas bloquer)
        migrations.AddField(
            model_name='role',
            name='django_group',
            field=models.OneToOneField(
                blank=True,
                editable=False,
                help_text="Groupe auth.Group synchronisé automatiquement — ne pas modifier manuellement.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='role_sgds',
                to='auth.group',
                verbose_name='Groupe Django natif',
            ),
        ),
    ]
