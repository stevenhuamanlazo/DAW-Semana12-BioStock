from django.contrib import admin
from django.urls import path

admin.site.site_header = "BioStock - Administración"
admin.site.site_title = "BioStock Admin"
admin.site.index_title = "Gestión de inventario de laboratorio"

urlpatterns = [
    path("admin/", admin.site.urls),
]