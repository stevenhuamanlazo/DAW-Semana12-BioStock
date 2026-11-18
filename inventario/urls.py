from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Autenticación
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),   # solo POST (Django 5)
    path("registro/", views.registro, name="registro"),
    # Productos
    path("productos/", views.producto_lista, name="producto_lista"),
    path("productos/nuevo/", views.ProductoCrearView.as_view(), name="producto_crear"),
    path("productos/<int:pk>/editar/", views.ProductoEditarView.as_view(), name="producto_editar"),
    path("productos/<int:pk>/baja/", views.producto_baja, name="producto_baja"),
    # Proveedores y movimientos
    path("proveedores/nuevo/", views.proveedor_crear, name="proveedor_crear"),
    path("movimientos/", views.movimiento_lista, name="movimiento_lista"),
    path("movimientos/nuevo/", views.movimiento_registrar, name="movimiento_registrar"),
]