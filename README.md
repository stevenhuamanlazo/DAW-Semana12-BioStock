# BioStock

**Gestión de Inventario de Suministros Médicos y Reactivos de Laboratorio**

Guía Práctica Semana 12 · Desarrollo de Aplicaciones Web (IS093A) · Universidad Nacional del Centro del Perú.

Sistema en Django 5 que controla productos con lote y fecha de vencimiento, alerta sobre productos vencidos, por vencer o con stock bajo, y registra entradas y salidas de inventario con trazabilidad del usuario.

## Funcionalidades por fase

| Fase | Contenido |
|---|---|
| 1. Formularios | ModelForm (producto, proveedor) y formulario clásico (movimientos), plantillas con `form.as_p`, `form.errors` y `csrf_token` |
| 2. Validación | `clean_<campo>()`, `clean()` cruzado, validadores regex (código BIO-0000, RUC) y `sanitize_input()` |
| 3. Django Admin | Filtros, búsqueda, campo calculado de estado, acciones masivas y campos sensibles ocultos |
| 4. Seguridad | Middleware de auditoría, sesiones seguras (30 min, HttpOnly, SameSite), login, registro, roles y permisos |
| 5. Auditoría | Cabeceras de seguridad, cookies Secure y `check --deploy` sin problemas con DEBUG=0 |

## Instalación

```powershell
git clone https://github.com/stevenhuamanlazo/DAW-Semana12-BioStock.git
cd DAW-Semana12-BioStock
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_catalogo
python manage.py setup_biostock
python manage.py createsuperuser
python manage.py runserver
```

Abrir http://127.0.0.1:8000/

## Roles y usuarios de demostración

| Usuario | Rol | Clave | Permisos |
|---|---|---|---|
| almacenero1 | Almacenero | BioStock#2026 | Ver productos y registrar movimientos |
| jefe1 | Jefe de laboratorio | BioStock#2026 | Además: crear, editar y dar de baja productos; crear proveedores |
| (createsuperuser) | Superusuario | la que defina | Django Admin completo |

Las claves anteriores son solo de demostración. Quien se registra desde `/registro/` recibe el rol Almacenero.

## Estructura

## Seguridad

- `DEBUG` y `SECRET_KEY` se leen del entorno (`DJANGO_DEBUG`, `DJANGO_SECRET_KEY`).
- Cookies HttpOnly, SameSite=Lax y Secure cuando `DEBUG=False`.
- Protección CSRF en todos los formularios POST, incluido el cierre de sesión.
- Registro de cada petición en `logs/auditoria.log`.

Verificación de despliegue:

```powershell
$env:DJANGO_DEBUG="0"; $env:DJANGO_SECRET_KEY=(python -c "import secrets;print(secrets.token_urlsafe(60))")
python manage.py check --deploy
```

## Uso de IA

Se utilizó Claude (Anthropic) como herramienta de apoyo para generar y explicar el código; el código fue ejecutado y verificado por el estudiante.

## Autor

Steven Huamanlazo Pariona · UNCP · IS093A