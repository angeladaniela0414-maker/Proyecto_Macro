"""Plantillas Jinja2 y utilidades de render (menú por rol, mensajes, token CSRF)."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

import config
import seguridad

templates = Jinja2Templates(directory=str(config.BASE_DIR / "templates"))

# (ruta, texto, icono Font Awesome)
MENUS = {
    "estudiante": [("/inicio", "Inicio", "fa-house"), ("/horario?mio=1", "Mi horario", "fa-calendar-days"),
                   ("/horario", "Consultar horarios", "fa-table-cells"), ("/salones", "Salones", "fa-door-open")],
    "docente": [("/inicio", "Inicio", "fa-house"), ("/horario?mio=1", "Mi horario", "fa-calendar-days"),
                ("/horario", "Horarios por nivel", "fa-table-cells"), ("/salones", "Salones", "fa-door-open")],
    "gestion": [("/inicio", "Inicio", "fa-house"), ("/gestion/generar", "Generar horarios", "fa-wand-magic-sparkles"),
                ("/horario", "Consultar horarios", "fa-table-cells"), ("/gestion/docentes", "Docentes", "fa-user-tie"),
                ("/gestion/estudiantes", "Estudiantes", "fa-user-graduate"), ("/salones", "Salones", "fa-door-open")],
}
ETIQUETAS = {"estudiante": "Portal estudiantil", "docente": "Portal docente", "gestion": "Gestión académica"}


def flash(request: Request, texto: str, tipo: str = "ok"):
    request.session.setdefault("flash", []).append([tipo, texto])


def _activo(request: Request, ruta: str, usuario: dict):
    path, _, query = ruta.partition("?")
    if request.url.path != path:
        return False
    if path == "/horario" and usuario["rol"] in ("estudiante", "docente"):
        es_mio = bool(request.query_params.get("mio")) or not request.query_params
        return es_mio == ("mio" in query)
    return True


def render(request: Request, nombre: str, status_code: int = 200, **contexto):
    u = seguridad.usuario_actual(request)
    contexto.update(
        usuario=u, csrf=seguridad.token_csrf(request), mensajes=request.session.pop("flash", []),
        etiqueta=ETIQUETAS.get(u["rol"], "") if u else "",
        menu=[(r, t, i, _activo(request, r, u)) for r, t, i in MENUS.get(u["rol"], [])] if u else [],
        nombre_completo=("%s %s" % (u["nombre"], u["apellido"])).strip() if u else "",
    )
    return templates.TemplateResponse(request, nombre, contexto, status_code=status_code)
