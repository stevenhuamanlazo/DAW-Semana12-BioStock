"""
Formularios de BioStock - Fase 1.

Ciclo de vida de un formulario:
    instanciación -> is_valid() -> cleaned_data -> save()
Regla de la guía: NUNCA guardar con request.POST directo; siempre Form(request.POST)
y llamar a is_valid() antes de guardar.
"""
from django import forms

from .models import MovimientoInventario, Producto, Proveedor


# ---------------------------------------------------------------------------
# 1) ModelForm: los campos se generan a partir del modelo Producto
# ---------------------------------------------------------------------------
class ProductoForm(forms.ModelForm):
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = Producto
        # Campos explícitos (nunca "__all__") para no exponer creado_por, activo, etc.
        fields = [
            "codigo", "nombre", "categoria", "proveedor", "lote",
            "fecha_vencimiento", "stock_actual", "stock_minimo", "cadena_frio",
        ]
        help_texts = {
            "codigo": "Formato BIO-0000. Ejemplo: BIO-0012.",
            "lote": "Obligatorio si hay stock o si requiere cadena de frío.",
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["razon_social", "ruc", "telefono", "correo"]


# ---------------------------------------------------------------------------
# 2) Formulario CLÁSICO (forms.Form): no está ligado a un modelo.
#    La vista decide cómo persistir los datos limpios (cleaned_data).
# ---------------------------------------------------------------------------
class MovimientoForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True).order_by("nombre"),
        label="Producto",
    )
    tipo = forms.ChoiceField(choices=MovimientoInventario.TIPOS, label="Tipo de movimiento")
    cantidad = forms.IntegerField(min_value=1, max_value=100000, label="Cantidad")
    motivo = forms.CharField(
        max_length=200, label="Motivo",
        widget=forms.TextInput(attrs={"placeholder": "Ej. Compra OC-2026-045, consumo en análisis..."}),
    )