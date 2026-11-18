"""
Validadores reutilizables y sanitización de entrada.

Validación en 3 niveles:
  1) Campo      -> validadores (aquí) y métodos clean_<campo>() del formulario
  2) Formulario -> método clean() para reglas que cruzan varios campos
  3) Modelo     -> validators= en los campos del modelo (última barrera)
"""
import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.html import strip_tags

# Código interno de producto: BIO- seguido de 4 dígitos (ej. BIO-0012)
validar_codigo = RegexValidator(
    regex=r"^BIO-\d{4}$",
    message="El código debe tener el formato BIO-0000 (ej. BIO-0012).",
    code="codigo_invalido",
)

# RUC peruano: exactamente 11 dígitos que empiezan con 10 o 20
validar_ruc = RegexValidator(
    regex=r"^(10|20)\d{9}$",
    message="El RUC debe tener 11 dígitos y empezar con 10 o 20.",
    code="ruc_invalido",
)

# Teléfono: opcional +51, de 6 a 9 dígitos
validar_telefono = RegexValidator(
    regex=r"^(\+51\s?)?\d{6,9}$",
    message="Ingrese un teléfono válido (6 a 9 dígitos, opcional +51).",
    code="telefono_invalido",
)


def validar_fecha_no_pasada(valor):
    """La fecha de vencimiento de un producto nuevo no puede estar en el pasado."""
    if valor < timezone.localdate():
        raise ValidationError(
            "La fecha de vencimiento ya pasó: no se puede ingresar un producto vencido.",
            code="fecha_pasada",
        )


def sanitize_input(texto):
    """
    Sanitización básica de texto antes de persistir.

    - strip_tags: elimina etiquetas HTML (<script>, <img onerror=...>) -> frena XSS almacenado.
    - elimina caracteres de control y colapsa espacios repetidos.
    - Las consultas SQL ya van parametrizadas por el ORM (previene SQLi).
    Nota: no se aplica escape() aquí porque la plantilla ya escapa al renderizar
    (autoescape); escapar dos veces mostraría &amp;lt; en pantalla.
    """
    if texto is None:
        return texto
    limpio = strip_tags(str(texto))
    limpio = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", limpio)
    limpio = re.sub(r"\s+", " ", limpio)
    return limpio.strip()