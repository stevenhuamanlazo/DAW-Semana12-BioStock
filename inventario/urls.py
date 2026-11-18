from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("productos/", views.producto_lista, name="producto_lista"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/baja/", views.producto_baja, name="producto_baja"),
    path("proveedores/nuevo/", views.proveedor_crear, name="proveedor_crear"),
    path("movimientos/", views.movimiento_lista, name="movimiento_lista"),
    path("movimientos/nuevo/", views.movimiento_registrar, name="movimiento_registrar"),
]