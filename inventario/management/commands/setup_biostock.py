from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

PERMISOS_ALMACENERO = [
    "view_producto", "view_categoria", "view_proveedor",
    "view_movimientoinventario", "add_movimientoinventario",
]
PERMISOS_JEFE = PERMISOS_ALMACENERO + [
    "add_producto", "change_producto", "delete_producto",
    "add_proveedor", "change_proveedor",
]
CLAVE_DEMO = "BioStock#2026"


class Command(BaseCommand):
    help = "Crea los roles (grupos con permisos) y usuarios de demostración."

    def handle(self, *args, **options):
        for nombre, codenames in (("Almacenero", PERMISOS_ALMACENERO),
                                  ("Jefe de laboratorio", PERMISOS_JEFE)):
            grupo, _ = Group.objects.get_or_create(name=nombre)
            grupo.permissions.set(Permission.objects.filter(
                content_type__app_label="inventario", codename__in=codenames))
            self.stdout.write(self.style.SUCCESS(f"Rol '{nombre}': {grupo.permissions.count()} permisos"))

        for username, nombres, apellidos, rol in (
            ("almacenero1", "Carlos", "Quispe", "Almacenero"),
            ("jefe1", "María", "Rojas", "Jefe de laboratorio"),
        ):
            user, creado = User.objects.get_or_create(username=username, defaults={
                "first_name": nombres, "last_name": apellidos, "email": f"{username}@biostock.example.pe"})
            if creado:
                user.set_password(CLAVE_DEMO)
                user.save()
            user.groups.set([Group.objects.get(name=rol)])
            self.stdout.write(f"Usuario {username} ({rol}) - clave: {CLAVE_DEMO}")