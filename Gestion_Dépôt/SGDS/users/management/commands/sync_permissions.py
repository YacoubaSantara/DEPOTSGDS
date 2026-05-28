"""
Synchronise auth.Permission avec le référentiel PERMISSIONS_REGISTRY,
puis synchronise les auth.Group Django natifs avec les Roles SGDS
(approche hybride RBAC ↔ Groups natifs).

À lancer après chaque ajout d'une nouvelle permission dans le code,
ou pour réparer une désynchronisation.

Usage : python manage.py sync_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = (
        "Synchronise les permissions du référentiel avec auth.Permission "
        "et met à jour les auth.Group liés aux Roles SGDS."
    )

    def handle(self, *args, **kwargs):
        from SGDS.users.models import UserProfile, Role
        from SGDS.users.permissions_registry import PERMISSIONS_REGISTRY

        ct = ContentType.objects.get_for_model(UserProfile)

        # ── Étape 1 : sync auth.Permission ────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[1/3] Synchronisation des auth.Permission..."
        ))

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

        orphelines = Permission.objects.filter(
            content_type=ct
        ).exclude(codename__in=codes_registre)
        for perm in orphelines:
            self.stdout.write(self.style.NOTICE(
                f"  [!] Orpheline (plus dans le registre) : {perm.codename}"
            ))

        # Garde-fou SUPERADMIN : toutes les permissions
        super_role = Role.objects.filter(code='SUPERADMIN').first()
        if super_role:
            toutes = Permission.objects.filter(codename__in=codes_registre)
            super_role.permissions.set(toutes)
            self.stdout.write(self.style.SUCCESS(
                f"  -> SUPERADMIN : {toutes.count()} permissions assignées"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] {crees} créées, {maj} mises à jour, "
            f"{orphelines.count()} orphelines."
        ))

        # ── Étape 2 : sync auth.Group ↔ Role ──────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[2/3] Synchronisation des auth.Group natifs..."
        ))

        groupes_crees, groupes_maj = 0, 0
        for role in Role.objects.all():
            group, created = Group.objects.get_or_create(name=role.code)

            # Lier le groupe au rôle si pas encore fait
            if role.django_group_id != group.pk:
                Role.objects.filter(pk=role.pk).update(django_group=group)
                self.stdout.write(
                    f"  {'+ Créé' if created else '~ Lié'} : Group '{role.code}' → Role '{role.nom}'"
                )
                if created:
                    groupes_crees += 1
                else:
                    groupes_maj += 1

            # Sync des permissions Role → Group
            group.permissions.set(role.permissions.all())

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] {groupes_crees} groupes créés, {groupes_maj} liés."
        ))

        # ── Étape 3 : sync membres (user.groups) ──────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[3/3] Synchronisation des membres (user ↔ group)..."
        ))

        from SGDS.users.models import UserProfile
        ids_groups_sgds = list(
            Role.objects.exclude(django_group__isnull=True)
                        .values_list('django_group_id', flat=True)
        )

        membres_sync = 0
        for profil in UserProfile.objects.select_related('role', 'user').all():
            user = profil.user
            # Retirer des groupes SGDS
            if ids_groups_sgds:
                user.groups.remove(*ids_groups_sgds)
            # Ajouter au bon groupe
            if profil.role and profil.role.django_group_id:
                user.groups.add(profil.role.django_group_id)
                membres_sync += 1

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] {membres_sync} utilisateurs synchronisés."
        ))

        self.stdout.write(self.style.SUCCESS(
            "\n✓ Synchronisation hybride RBAC ↔ Groups terminée."
        ))
