from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_backfill_depot_vers_depots'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='depot',
        ),
    ]
