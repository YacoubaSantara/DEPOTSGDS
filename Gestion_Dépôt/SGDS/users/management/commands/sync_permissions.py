"""
Synchronise auth.Permission avec le référentiel PERMISSIONS_REGISTRY.
À lancer après chaque ajout d'une nouvelle permission dans le code.

Usage : python manage.py sync_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Synchronise les permissions du référentiel avec auth.Permission"

    def handle(self, *args, **kwargs):
        from SGDS.users.models import UserProfile, Role
        from SGDS.users.permissions_registry import PERMISSIONS_REGISTRY

        ct = ContentType.objects.get_for_model(UserProfile)

        codes_registre = set()
        crees, maj = 0, 0

        for groupe in PERMISSIONS_REGISTRY.values():
            for codename, libelle in groupe['permissions']:
                codes_registre.add(codename)
                perm, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=ct,
                    defaults={'name': libelle},
                )
                if created:
                    crees += 1
                    self.stdout.write(self.style.SUCCESS(f"  + {codename}"))
                elif perm.name != libelle:
                    perm.name = libelle
                    perm.save()
                    maj += 1
                    self.stdout.write(self.style.WARNING(f"  ~ {codename}"))

        # Permissions orphelines (dans la base mais plus dans le registre)
        orphelines = Permission.objects.filter(
            content_type=ct
        ).exclude(codename__in=codes_registre)
        for perm in orphelines:
            self.stdout.write(self.style.NOTICE(
                f"  [!] Orpheline (plus dans le registre) : {perm.codename}"
            ))

        # Garde-fou SUPERADMIN
        super_role = Role.objects.filter(code='SUPERADMIN').first()
        if super_role:
            toutes = Permission.objects.filter(codename__in=codes_registre)
            super_role.permissions.set(toutes)
            self.stdout.write(self.style.SUCCESS(
                f"\n-> SUPERADMIN : {toutes.count()} permissions assignees"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] {crees} crees, {maj} mis a jour, "
            f"{orphelines.count()} orphelines."
        ))
