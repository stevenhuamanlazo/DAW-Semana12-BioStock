from django.db import transaction
from django.db.models import F

from .models import MovimientoInventario, Producto


@transaction.atomic
def registrar_movimiento(*, producto, tipo, cantidad, motivo, usuario):
    """
    Registra el movimiento y actualiza el stock en una sola transacción.
    Se bloquea la fila del producto para evitar condiciones de carrera
    (dos usuarios sacando stock al mismo tiempo).
    """
    producto = Producto.objects.select_for_update().get(pk=producto.pk)
    if tipo == MovimientoInventario.SALIDA:
        if cantidad > producto.stock_actual:
            raise ValueError("Stock insuficiente.")
        Producto.objects.filter(pk=producto.pk).update(stock_actual=F("stock_actual") - cantidad)
    else:
        Producto.objects.filter(pk=producto.pk).update(stock_actual=F("stock_actual") + cantidad)

    return MovimientoInventario.objects.create(
        producto=producto, tipo=tipo, cantidad=cantidad, motivo=motivo, usuario=usuario,
    )