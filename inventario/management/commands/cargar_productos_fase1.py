"""
Carga productos y movimientos de ejemplo usando los formularios reales
(ProductoForm y MovimientoForm), igual que si se llenaran en el navegador.
Es idempotente: si el código o el movimiento ya existen, los omite.
Solo para la Fase 1: en la Fase 2 el sistema rechazará productos vencidos.
"""
from datetime import date

from django.core.management.base import BaseCommand

from inventario.forms import MovimientoForm, ProductoForm
from inventario.models import Categoria, MovimientoInventario, Producto, Proveedor
from inventario.services import registrar_movimiento

PRODUCTOS = [
    # codigo, nombre, categoria, ruc proveedor, lote, vence, stock, minimo, frio
    ("BIO-0001", "Ácido clorhídrico 37%", "Reactivo químico", "20100123456", "LT-2026-01", date(2027, 5, 30), 47, 10, True),
    ("BIO-0002", "Kit ELISA VIH", "Reactivo biológico", "20551234567", "ELI-0456", date(2026, 12, 10), 8, 10, True),
    ("BIO-0003", "Guantes de nitrilo talla M", "Insumo médico", "20601234568", "GN-2026-77", date(2028, 3, 15), 200, 50, False),
    ("BIO-0004", "Placas Petri 90 mm", "Material de vidrio", "20601234568", "PP-1120", date(2027, 1, 20), 120, 30, False),
    ("BIO-0005", "Suero control nivel 2", "Reactivo biológico", "20551234567", "SC-0099", date(2026, 10, 15), 15, 5, True),
]

MOVIMIENTOS = [
    ("BIO-0001", "SALIDA", 5, "Consumo en análisis de pH - Laboratorio 2"),
    ("BIO-0003", "ENTRADA", 100, "Compra OC-2026-045"),
]


class Command(BaseCommand):
    help = "Crea productos y movimientos de ejemplo a través de los formularios."

    def handle(self, *args, **options):
        for cod, nombre, cat, ruc, lote, vence, stock, minimo, frio in PRODUCTOS:
            if Producto.objects.filter(codigo=cod).exists():
                self.stdout.write(f"  {cod}: ya existe, se omite")
                continue
            datos = {
                "codigo": cod, "nombre": nombre,
                "categoria": Categoria.objects.get(nombre=cat).pk,
                "proveedor": Proveedor.objects.get(ruc=ruc).pk,
                "lote": lote, "fecha_vencimiento": vence.isoformat(),
                "stock_actual": stock, "stock_minimo": minimo,
            }
            if frio:
                datos["cadena_frio"] = "on"
            form = ProductoForm(datos)              # el mismo ciclo de la vista
            if form.is_valid():
                form.save()
                self.stdout.write(self.style.SUCCESS(f"  {cod}: creado"))
            else:
                self.stdout.write(self.style.ERROR(f"  {cod}: {form.errors.as_json()}"))

        for cod, tipo, cantidad, motivo in MOVIMIENTOS:
            if MovimientoInventario.objects.filter(motivo=motivo).exists():
                self.stdout.write(f"  Movimiento '{motivo}': ya existe, se omite")
                continue
            producto = Producto.objects.filter(codigo=cod, activo=True).first()
            if not producto:
                continue
            form = MovimientoForm({"producto": producto.pk, "tipo": tipo,
                                   "cantidad": cantidad, "motivo": motivo})
            if form.is_valid():
                d = form.cleaned_data
                registrar_movimiento(producto=d["producto"], tipo=d["tipo"],
                                     cantidad=d["cantidad"], motivo=d["motivo"], usuario=None)
                self.stdout.write(self.style.SUCCESS(f"  Movimiento {tipo} {cantidad} x {cod}: registrado"))
            else:
                self.stdout.write(self.style.ERROR(f"  Movimiento {cod}: {form.errors.as_json()}"))