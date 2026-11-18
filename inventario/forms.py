"""
Formularios de BioStock - Fase 2 (validación y sanitización).

Validación en 3 niveles:
  1) Campo      -> clean_<campo>() y validadores (validators.py)
  2) Formulario -> clean() para reglas que cruzan varios campos
  3) Modelo     -> validators= en los campos del modelo (se ejecutan en _post_clean)

Orden real de ejecución al llamar is_valid():
  campo.clean() -> clean_<campo>() (por cada campo) -> clean() -> validación del modelo
"""
from django import forms

from .models import MovimientoInventario, Producto, Proveedor
from .validators import sanitize_input, validar_fecha_no_pasada


# ---------------------------------------------------------------------------
# 1) ModelForm: Producto
# ---------------------------------------------------------------------------
class ProductoForm(forms.ModelForm):
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = Producto
        fields = [
            "codigo", "nombre", "categoria", "proveedor", "lote",
            "fecha_vencimiento", "stock_actual", "stock_minimo", "cadena_frio",
        ]
        labels = {
            "codigo": "Código",
            "nombre": "Nombre del producto",
            "categoria": "Categoría",
            "stock_actual": "Stock actual",
            "stock_minimo": "Stock mínimo",
        }
        help_texts = {
            "codigo": "Formato BIO-0000. Ejemplo: BIO-0012.",
            "lote": "Obligatorio si hay stock o si requiere cadena de frío.",
        }

    # -- Nivel 1: validación por campo -------------------------------------
    def clean_codigo(self):
        # Sanitiza y normaliza a mayúsculas; el regex BIO-0000 lo valida el modelo.
        return sanitize_input(self.cleaned_data["codigo"]).upper()

    def clean_nombre(self):
        nombre = sanitize_input(self.cleaned_data["nombre"])  # quita <script>, etc.
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre

    def clean_lote(self):
        return sanitize_input(self.cleaned_data.get("lote", "")).upper()

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data["fecha_vencimiento"]
        # En edición solo se valida si el usuario cambió la fecha; así se puede
        # corregir un producto que ya venció sin que el formulario lo bloquee.
        if not self.instance.pk or fecha != self.instance.fecha_vencimiento:
            validar_fecha_no_pasada(fecha)
        return fecha

    # -- Nivel 2: validación cruzada ---------------------------------------
    def clean(self):
        # IA: ¿por qué cleaned_data no tiene un campo dentro de clean()? →
        # Solución manual: clean() se ejecuta aunque un campo haya fallado; ese
        # campo no está en cleaned_data. Por eso se usa .get() en lugar de [].
        cleaned = super().clean()
        stock = cleaned.get("stock_actual")
        minimo = cleaned.get("stock_minimo")
        lote = cleaned.get("lote")
        frio = cleaned.get("cadena_frio")

        # add_error(): error asociado a UN campo; el formulario sigue validando.
        if frio and not lote:
            self.add_error("lote", "Un producto con cadena de frío debe registrar su lote.")
        if minimo is not None and minimo > 5000:
            self.add_error("stock_minimo", "El stock mínimo no puede superar 5000 unidades.")

        # ValidationError en clean(): error general (__all__ / non_field_errors).
        if stock and stock > 0 and not lote and not frio:
            raise forms.ValidationError(
                "Un producto con stock debe tener lote registrado para su trazabilidad."
            )
        return cleaned


# ---------------------------------------------------------------------------
# 2) ModelForm: Proveedor
# ---------------------------------------------------------------------------
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["razon_social", "ruc", "telefono", "correo"]
        labels = {
            "razon_social": "Razón social",
            "ruc": "RUC",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
        }
        help_texts = {"ruc": "11 dígitos; empieza con 10 (persona) o 20 (empresa)."}

    def clean_razon_social(self):
        razon = sanitize_input(self.cleaned_data["razon_social"])
        if len(razon) < 3:
            raise forms.ValidationError("La razón social es muy corta.")
        return razon.upper()

    def clean_correo(self):
        return sanitize_input(self.cleaned_data.get("correo", "")).lower()


# ---------------------------------------------------------------------------
# 3) Formulario CLÁSICO: movimiento de inventario
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

    def clean_motivo(self):
        motivo = sanitize_input(self.cleaned_data["motivo"])
        if len(motivo) < 5:
            raise forms.ValidationError("Describa el motivo (mínimo 5 caracteres).")
        return motivo

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get("producto")
        tipo = cleaned.get("tipo")
        cantidad = cleaned.get("cantidad")
        if not (producto and tipo and cantidad):
            return cleaned  # ya hay errores de campo; no tiene sentido seguir

        if tipo == MovimientoInventario.SALIDA:
            if cantidad > producto.stock_actual:
                self.add_error(
                    "cantidad",
                    f"Stock insuficiente: hay {producto.stock_actual} unidades de {producto.codigo}.",
                )
            if producto.estado == Producto.ESTADO_VENCIDO:
                raise forms.ValidationError(
                    f"{producto.codigo} está vencido: debe darse de baja, no consumirse."
                )
        return cleaned