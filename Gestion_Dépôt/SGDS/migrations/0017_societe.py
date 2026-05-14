"""
Migration 0017 : Crée la table SGDS_Societe (singleton fiche dépôt).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0016_data_migration_lignes_mouvement'),
    ]

    operations = [
        migrations.CreateModel(
            name='Societe',
            fields=[
                ('id',                 models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raison_sociale',     models.CharField(max_length=200, verbose_name='Raison sociale')),
                ('sigle',              models.CharField(blank=True, max_length=50, null=True, verbose_name='Sigle / Abréviation')),
                ('forme_juridique',    models.CharField(blank=True, max_length=10, null=True, verbose_name='Forme juridique')),
                ('numero_contribuable',models.CharField(blank=True, max_length=100, null=True, verbose_name='N° Contribuable / NIF')),
                ('numero_ifu',         models.CharField(blank=True, max_length=100, null=True, verbose_name='N° IFU')),
                ('capital_social',     models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Capital social (FCFA)')),
                ('logo',               models.ImageField(blank=True, null=True, upload_to='societe/', verbose_name='Logo')),
                ('tampon',             models.ImageField(blank=True, null=True, upload_to='societe/', verbose_name='Tampon / Cachet')),
                ('couleur_principale', models.CharField(blank=True, default='#1e3a5f', max_length=7, verbose_name='Couleur principale (hex)')),
                ('pied_de_page',       models.TextField(blank=True, null=True, verbose_name='Texte pied de page des états')),
                ('adresse',            models.TextField(blank=True, null=True, verbose_name='Adresse complète')),
                ('ville',              models.CharField(blank=True, max_length=100, null=True, verbose_name='Ville')),
                ('pays',               models.CharField(default='Mali', max_length=100, verbose_name='Pays')),
                ('boite_postale',      models.CharField(blank=True, max_length=50, null=True, verbose_name='Boîte postale')),
                ('telephone',          models.CharField(blank=True, max_length=20, null=True, verbose_name='Téléphone principal')),
                ('telephone2',         models.CharField(blank=True, max_length=20, null=True, verbose_name='Téléphone secondaire')),
                ('email',              models.EmailField(blank=True, null=True, verbose_name='Email')),
                ('site_web',           models.URLField(blank=True, null=True, verbose_name='Site web')),
                ('nom_depot',          models.CharField(default='SGDS SANKE', max_length=200, verbose_name='Nom du dépôt')),
                ('type_depot',         models.CharField(default='Dépôt de droit', max_length=100, verbose_name='Type de dépôt')),
                ('numero_agrement',    models.CharField(blank=True, max_length=100, null=True, verbose_name="N° Agrément")),
                ('autorite_tutelle',   models.CharField(blank=True, max_length=200, null=True, verbose_name='Autorité de tutelle')),
                ('date_creation',      models.DateField(blank=True, null=True, verbose_name='Date de création')),
                ('date_modification',  models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
            ],
            options={
                'verbose_name': 'Société / Dépôt',
                'verbose_name_plural': 'Société / Dépôt',
            },
        ),
    ]
