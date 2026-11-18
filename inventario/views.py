"""Vistas de BioStock - Fase 1 (formularios y plantillas)."""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MovimientoForm, ProductoForm, ProveedorForm
from .models import MovimientoInventario, Producto
from .services import registrar_movimiento


def inicio(request):
    return redirect("producto_lista")


def producto_lista(request):
    q = request.GET.get("q", "").strip()
    # select_related evita el problema N+1: trae categoría y proveedor en 1 sola consulta
    productos = Producto.objects.filter(activo=True).select_related("categoria", "proveedor")
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(codigo__icontains=q) | Q(lote__icontains=q)
        )
    return render(request, "inventario/producto_lista.html", {"productos": productos, "q": q})


def producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)       # instanciación con datos
        if form.is_valid():                     # validación
            producto = form.save()              # guardado (solo si es válido)
            messages.success(request, f"Producto {producto.codigo} registrado correctamente.")
            return redirect("producto_lista")
    else:
        form = ProductoForm()                   # formulario vacío (GET)
    return render(request, "inventario/form_generico.html",
                  {"form": form, "titulo": "Nuevo producto"})


def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto {producto.codigo} actualizado.")
            return redirect("producto_lista")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "inventario/form_generico.html",
                  {"form": form, "titulo": f"Editar {producto.codigo}"})


def producto_baja(request, pk):
    """Baja lógica: se conserva el historial de movimientos (auditoría)."""
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo"])
        messages.warning(request, f"Producto {producto.codigo} dado de baja.")
        return redirect("producto_lista")
    return render(request, "inventario/producto_baja.html", {"producto": producto})


def proveedor_crear(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f"Proveedor {proveedor.razon_social} registrado.")
            return redirect("producto_lista")
    else:
        form = ProveedorForm()
    return render(request, "inventario/form_generico.html",
                  {"form": form, "titulo": "Nuevo proveedor"})


def movimiento_registrar(request):
    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data           # datos ya limpios y tipados
            try:
                registrar_movimiento(
                    producto=datos["producto"], tipo=datos["tipo"],
                    cantidad=datos["cantidad"], motivo=datos["motivo"],
                    usuario=request.user if request.user.is_authenticated else None,
                )
            except ValueError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, "Movimiento registrado y stock actualizado.")
                return redirect("movimiento_lista")
    else:
        form = MovimientoForm()
    return render(request, "inventario/form_generico.html",
                  {"form": form, "titulo": "Registrar movimiento de inventario"})


def movimiento_lista(request):
    movimientos = MovimientoInventario.objects.select_related("producto", "usuario")[:100]
    return render(request, "inventario/movimiento_lista.html", {"movimientos": movimientos})