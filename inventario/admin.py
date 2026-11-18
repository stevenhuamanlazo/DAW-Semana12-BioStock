from django.contrib import admin

from .models import Categoria, MovimientoInventario, Producto, Proveedor

# Registro mínimo (Fase 1). En la Fase 3 se personaliza con ModelAdmin.
admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Producto)
admin.site.register(MovimientoInventario)