from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .validators import validar_codigo, validar_ruc, validar_telefono

DIAS_ALERTA_VENCIMIENTO = 30


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    razon_social = models.CharField(max_length=150)
    ruc = models.CharField(max_length=11, unique=True, validators=[validar_ruc])
    telefono = models.CharField(max_length=15, blank=True, validators=[validar_telefono])
    correo = models.EmailField(blank=True)

    class Meta:
        ordering = ["razon_social"]
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return f"{self.razon_social} ({self.ruc})"


class Producto(models.Model):
    """Suministro médico o reactivo de laboratorio."""

    ESTADO_VIGENTE = "VIGENTE"
    ESTADO_POR_VENCER = "POR_VENCER"
    ESTADO_VENCIDO = "VENCIDO"

    codigo = models.CharField(max_length=8, unique=True, validators=[validar_codigo])
    nombre = models.CharField(max_length=150)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="productos")
    lote = models.CharField(max_length=40, blank=True)
    fecha_vencimiento = models.DateField()
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=10)
    cadena_frio = models.BooleanField("requiere cadena de frío", default=False)
    requiere_reposicion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="productos_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_vencimiento", "nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def estado(self):
        """Estado calculado según la fecha de vencimiento."""
        hoy = timezone.localdate()
        if self.fecha_vencimiento < hoy:
            return self.ESTADO_VENCIDO
        if self.fecha_vencimiento <= hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO):
            return self.ESTADO_POR_VENCER
        return self.ESTADO_VIGENTE

    @property
    def estado_texto(self):
        return {
            self.ESTADO_VIGENTE: "Vigente",
            self.ESTADO_POR_VENCER: "Por vencer",
            self.ESTADO_VENCIDO: "Vencido",
        }[self.estado]

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo


class MovimientoInventario(models.Model):
    """Entrada o salida de stock. Es un registro de auditoría: no se edita."""

    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    TIPOS = [(ENTRADA, "Entrada"), (SALIDA, "Salida")]

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=7, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=200)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="movimientos",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad} x {self.producto.codigo}"