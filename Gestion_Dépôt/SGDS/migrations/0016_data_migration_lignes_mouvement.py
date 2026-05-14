"""
Migration de données : convertit les Mouvement existants (avec FK cuve simple)
en LigneMouvement (1 ligne par mouvement avec cuve renseignée).
"""
from django.db import migrations


def creer_lignes_depuis_mouvements(apps, schema_editor):
    Mouvement = apps.get_model('SGDS', 'Mouvement')
    LigneMouvement = apps.get_model('SGDS', 'LigneMouvement')

    lignes = []
    for m in Mouvement.objects.select_related('cuve', 'produit').filter(cuve__isnull=False):
        type_m = m.type_mouvement
        if type_m == 'ENTREE':
            vol_amb = m.volume_ambiant_recu
            vol_15c = m.volume_15c_recu
        elif type_m == 'SORTIE':
            vol_amb = m.volume_ambiant_sortie
            vol_15c = m.volume_15c_sortie
        elif type_m == 'CESSION':
            vol_amb = m.cession_volume_ambiant
            vol_15c = m.cession_volume_15c
        elif type_m == 'ACQUITTEMENT':
            vol_amb = m.acquittement_volume_ambiant
            vol_15c = m.acquittement_volume_15c
        else:
            vol_amb = None
            vol_15c = None

        lignes.append(LigneMouvement(
            mouvement=m,
            cuve=m.cuve,
            produit=m.produit,
            volume_ambiant=vol_amb,
            volume_15c=vol_15c,
            ordre=1,
        ))

    LigneMouvement.objects.bulk_create(lignes)


def annuler_lignes(apps, schema_editor):
    LigneMouvement = apps.get_model('SGDS', 'LigneMouvement')
    LigneMouvement.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0015_lignemouvement'),
    ]

    operations = [
        migrations.RunPython(creer_lignes_depuis_mouvements, annuler_lignes),
    ]
