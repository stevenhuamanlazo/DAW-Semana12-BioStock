"""
Middleware propio de BioStock (Fase 4).

Un middleware es un callable con __init__(get_response) y __call__(request).
Flujo:  request -> [middlewares hacia abajo] -> vista -> [middlewares hacia arriba] -> response
Debe devolver siempre una respuesta (la que entrega get_response).
"""
import logging
import time
import uuid

logger = logging.getLogger("biostock.auditoria")


class AuditoriaMiddleware:
    """
    Registra cada petición en logs/auditoria.log:
    id de petición, usuario, método, ruta, estado HTTP, duración e IP.
    También guarda en la sesión la última actividad del usuario.
    """

    def __init__(self, get_response):
        # Se ejecuta UNA vez al iniciar el servidor.
        self.get_response = get_response

    def __call__(self, request):
        # --- Código antes de la vista ---
        inicio = time.perf_counter()
        request.id_peticion = uuid.uuid4().hex[:8]

        response = self.get_response(request)

        # --- Código después de la vista ---
        duracion_ms = (time.perf_counter() - inicio) * 1000
        usuario = request.user.get_username() if request.user.is_authenticated else "anonimo"

        # Regla de la guía: al escribir en request.session hay que marcar
        # modified = True para que Django persista el cambio.
        if request.user.is_authenticated:
            request.session["ultima_actividad"] = time.strftime("%Y-%m-%d %H:%M:%S")
            request.session["ultima_ruta"] = request.path
            request.session.modified = True

        logger.info(
            "id=%s | user=%s | %s %s | status=%s | %.1fms | ip=%s",
            request.id_peticion, usuario, request.method, request.get_full_path(),
            response.status_code, duracion_ms, self._ip(request),
        )
        response["X-Request-ID"] = request.id_peticion
        return response

    @staticmethod
    def _ip(request):
        return request.META.get("REMOTE_ADDR", "-")


class CabecerasSeguridadMiddleware:
    """Añade cabeceras de seguridad a TODAS las respuestas."""

    CSP = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self.CSP)
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response