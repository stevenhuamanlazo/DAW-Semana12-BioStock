"""Vistas de BioStock: formularios, autenticación y autorización (Fases 1 y 4)."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView

from .forms import MovimientoForm, ProductoForm, ProveedorForm
from .forms_usuarios import RegistroForm
from .models import DIAS_ALERTA_VENCIMIENTO, MovimientoInventario, Producto
from .services import registrar_movimiento


def inicio(request):
    return redirect("dashboard")


def registro(request):
    """Registro público: el usuario nuevo recibe el rol 'Almacenero'."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada. Ya puede iniciar sesión.")
            return redirect("login")
    else:
        form = RegistroForm()
    return render(request, "registration/registro.html", {"form": form})


@login_required
def dashboard(request):
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
    activos = Producto.objects.filter(activo=True).select_related("categoria", "proveedor")
    vencidos = activos.filter(fecha_vencimiento__lt=hoy)
    por_vencer = activos.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite)
    bajo_stock = activos.filter(stock_actual__lte=F("stock_minimo"))
    contexto = {
        "total": activos.count(),
        "vencidos": vencidos, "por_vencer": por_vencer, "bajo_stock": bajo_stock,
        "ultimos": MovimientoInventario.objects.select_related("producto", "usuario")[:5],
        # Datos de la sesión (los escribe AuditoriaMiddleware)
        "ultima_actividad": request.session.get("ultima_actividad"),
        "expira_en_min": request.session.get_expiry_age() // 60,
    }
    return render(request, "inventario/dashboard.html", contexto)


# -- Productos ----------------------------------------------------------------
@login_required
@permission_required("inventario.view_producto", raise_exception=True)
def producto_lista(request):
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.filter(activo=True).select_related("categoria", "proveedor")
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(codigo__icontains=q) | Q(lote__icontains=q))
    return render(request, "inventario/producto_lista.html", {"productos": productos, "q": q})


class ProductoCrearView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista basada en clase protegida con PermissionRequiredMixin."""
    model = Producto
    form_class = ProductoForm
    template_name = "inventario/form_generico.html"
    permission_required = "inventario.add_producto"
    success_url = reverse_lazy("producto_lista")
    extra_context = {"titulo": "Nuevo producto"}

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, f"Producto {form.instance.codigo} registrado correctamente.")
        return super().form_valid(form)


class ProductoEditarView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    form_class = ProductoForm
    template_name = "inventario/form_generico.html"
    permission_required = "inventario.change_producto"
    success_url = reverse_lazy("producto_lista")

    def get_queryset(self):
        return Producto.objects.filter(activo=True)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = f"Editar {self.object.codigo}"
        return contexto

    def form_valid(self, form):
        messages.success(self.request, f"Producto {form.instance.codigo} actualizado.")
        return super().form_valid(form)


@login_required
@permission_required("inventario.delete_producto", raise_exception=True)
def producto_baja(request, pk):
    """Baja lógica: se conserva el historial de movimientos (auditoría)."""
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo"])
        messages.warning(request, f"Producto {producto.codigo} dado de baja.")
        return redirect("producto_lista")
    return render(request, "inventario/producto_baja.html", {"producto": producto})


# -- Proveedores --------------------------------------------------------------
@login_required
@permission_required("inventario.add_proveedor", raise_exception=True)
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


# -- Movimientos --------------------------------------------------------------
@login_required
@permission_required("inventario.add_movimientoinventario", raise_exception=True)
def movimiento_registrar(request):
    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                registrar_movimiento(
                    producto=datos["producto"], tipo=datos["tipo"], cantidad=datos["cantidad"],
                    motivo=datos["motivo"], usuario=request.user)
            except ValueError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, "Movimiento registrado y stock actualizado.")
                return redirect("movimiento_lista")
    else:
        form = MovimientoForm()
    return render(request, "inventario/form_generico.html",
                  {"form": form, "titulo": "Registrar movimiento de inventario"})


@login_required
@permission_required("inventario.view_movimientoinventario", raise_exception=True)
def movimiento_lista(request):
    movimientos = MovimientoInventario.objects.select_related("producto", "usuario")[:100]
    return render(request, "inventario/movimiento_lista.html", {"movimientos": movimientos})