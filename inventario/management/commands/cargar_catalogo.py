from django.core.management.base import BaseCommand

from inventario.models import Categoria, Proveedor


class Command(BaseCommand):
    help = "Carga categorías y proveedores base de BioStock (idempotente)."

    def handle(self, *args, **options):
        categorias = [
            ("Reactivo químico", "Ácidos, bases y soluciones de laboratorio"),
            ("Reactivo biológico", "Anticuerpos, kits ELISA, medios de cultivo"),
            ("Insumo médico", "Jeringas, gasas, guantes, mascarillas"),
            ("Material de vidrio", "Tubos, placas Petri, matraces"),
        ]
        for nombre, descripcion in categorias:
            Categoria.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})

        proveedores = [
            ("MERCK PERU S.A.", "20100123456", "014567890", "ventas@merck.example.pe"),
            ("BIOMEDICAL SUPPLY E.I.R.L.", "20551234567", "987654321", "contacto@biomedsupply.example.pe"),
            ("LABORATORIOS ANDINOS S.A.C.", "20601234568", "012345678", "pedidos@labandinos.example.pe"),
        ]
        for razon, ruc, tel, correo in proveedores:
            Proveedor.objects.get_or_create(
                ruc=ruc, defaults={"razon_social": razon, "telefono": tel, "correo": correo}
            )
        self.stdout.write(self.style.SUCCESS(
            f"Catálogo listo: {Categoria.objects.count()} categorías, {Proveedor.objects.count()} proveedores."
        ))