"""
Django Admin personalizado (Fase 3).
El Admin es una app Django completa: cada ModelAdmin sobrescribe su comportamiento.
"""
from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html

from .models import (DIAS_ALERTA_VENCIMIENTO, Categoria, MovimientoInventario,
                     Producto, Proveedor)


# ---------------------------------------------------------------------------
# Filtro personalizado por estado de vencimiento
# ---------------------------------------------------------------------------
class EstadoVencimientoFilter(admin.SimpleListFilter):
    title = "estado de vencimiento"
    parameter_name = "estado"

    def lookups(self, request, model_admin):
        return [("vencido", "Vencido"), ("por_vencer", "Por vencer (30 días)"), ("vigente", "Vigente")]

    def queryset(self, request, queryset):
        hoy = timezone.localdate()
        limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
        if self.value() == "vencido":
            return queryset.filter(fecha_vencimiento__lt=hoy)
        if self.value() == "por_vencer":
            return queryset.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite)
        if self.value() == "vigente":
            return queryset.filter(fecha_vencimiento__gt=limite)
        return queryset


# ---------------------------------------------------------------------------
# Acciones masivas: reciben (modeladmin, request, queryset)
# ---------------------------------------------------------------------------
@admin.action(description="Marcar seleccionados para reposición")
def marcar_reposicion(modeladmin, request, queryset):
    n = queryset.update(requiere_reposicion=True)
    modeladmin.message_user(request, f"{n} producto(s) marcados para reposición.")


@admin.action(description="Quitar marca de reposición")
def quitar_reposicion(modeladmin, request, queryset):
    n = queryset.update(requiere_reposicion=False)
    modeladmin.message_user(request, f"Se quitó la marca a {n} producto(s).")


@admin.action(description="Dar de baja productos seleccionados")
def dar_de_baja(modeladmin, request, queryset):
    n = queryset.update(activo=False)
    modeladmin.message_user(request, f"{n} producto(s) dados de baja.")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "ruc", "telefono", "correo")
    search_fields = ("razon_social", "ruc")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "proveedor", "stock_actual",
                    "stock_minimo", "fecha_vencimiento", "estado_coloreado",
                    "cadena_frio", "requiere_reposicion", "activo")
    list_filter = (EstadoVencimientoFilter, "categoria", "proveedor", "cadena_frio",
                  "requiere_reposicion", "activo")
    search_fields = ("codigo", "nombre", "lote", "proveedor__razon_social")
    list_select_related = ("categoria", "proveedor")      # evita N+1 en la lista
    list_per_page = 20
    date_hierarchy = "fecha_vencimiento"
    actions = [marcar_reposicion, quitar_reposicion, dar_de_baja]
    # readonly_fields NO se guardan en la base de datos
    readonly_fields = ("estado_coloreado", "creado_por", "creado_en")
    fieldsets = (
        ("Identificación", {"fields": ("codigo", "nombre", "categoria", "proveedor")}),
        ("Trazabilidad", {"fields": ("lote", "fecha_vencimiento", "estado_coloreado", "cadena_frio")}),
        ("Inventario", {"fields": ("stock_actual", "stock_minimo", "requiere_reposicion", "activo")}),
        ("Auditoría", {"fields": ("creado_por", "creado_en")}),
    )

    @admin.display(description="Estado", ordering="fecha_vencimiento")
    def estado_coloreado(self, obj):
        """Campo calculado: se muestra como columna aunque no exista en la BD."""
        colores = {Producto.ESTADO_VIGENTE: "#166534", Producto.ESTADO_POR_VENCER: "#b45309",
                   Producto.ESTADO_VENCIDO: "#b91c1c"}
        return format_html('<b style="color:{}">{}</b>', colores[obj.estado], obj.estado_texto)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user           # auditoría: quién lo creó
        super().save_model(request, obj, form, change)


@admin.register(MovimientoInventario)
class MovimientoAdmin(admin.ModelAdmin):
    """Los movimientos son un registro de auditoría: solo lectura."""
    list_display = ("fecha", "producto", "tipo", "cantidad", "usuario", "motivo")
    list_filter = ("tipo", "fecha")
    search_fields = ("producto__codigo", "producto__nombre", "motivo", "usuario__username")
    list_select_related = ("producto", "usuario")
    date_hierarchy = "fecha"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Usuarios: NUNCA exponer password, is_staff, is_superuser ni user_permissions
# ---------------------------------------------------------------------------
admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "email", "rol", "is_active")
    list_filter = ("groups", "is_active")
    fieldsets = (
        (None, {"fields": ("username",)}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email")}),
        ("Acceso", {"fields": ("groups", "is_active")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(description="Rol")
    def rol(self, obj):
        return ", ".join(g.name for g in obj.groups.all()) or "-"