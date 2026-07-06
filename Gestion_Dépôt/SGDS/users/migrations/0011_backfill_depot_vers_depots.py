from django.db import migrations


def copier_depot_vers_depots(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    for profil in UserProfile.objects.exclude(depot__isnull=True):
        profil.depots.add(profil.depot_id)


def revenir_en_arriere(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    for profil in UserProfile.objects.all():
        premier = profil.depots.first()
        if premier is not None:
            profil.depot_id = premier.pk
            profil.save(update_fields=['depot'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_userprofile_depots_m2m'),
    ]

    operations = [
        migrations.RunPython(copier_depot_vers_depots, revenir_en_arriere),
    ]
