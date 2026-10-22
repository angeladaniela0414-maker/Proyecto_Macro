"""Sistema de horarios ULEAM (FastAPI).  Ejecutar:  python main.py   (puerto 80: como Administrador)."""
import logging
import socket
from urllib.parse import quote

import pyodbc
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

import config
from plantillas import render
from rutas import auth, gestion, vistas
from seguridad import IrALogin

app = FastAPI(title="Horarios ULEAM", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie="horarios_uleam",
                   max_age=config.DIAS_RECORDAR * 86400, same_site="lax", https_only=False)
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "static")), name="static")
for modulo in (auth, vistas, gestion):
    app.include_router(modulo.router)


def _pagina_error(request: Request, codigo, titulo, detalle):
    return render(request, "error.html", status_code=codigo, codigo=codigo, titulo=titulo, detalle=detalle)


@app.exception_handler(IrALogin)
async def ir_a_login(request: Request, exc: IrALogin):
    destino = "/login" + ("?siguiente=" + quote(exc.destino) if exc.destino else "")
    return RedirectResponse(destino, status_code=303)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    textos = {400: ("Solicitud no válida", "El formulario expiró. Recarga la página e inténtalo de nuevo."),
              403: ("Sin permiso", "Tu rol no tiene acceso a esta sección."),
              404: ("Página no encontrada", "La dirección no existe o fue movida.")}
    titulo, detalle = textos.get(exc.status_code, ("Error", str(exc.detail)))
    return _pagina_error(request, exc.status_code, titulo, detalle)


@app.exception_handler(pyodbc.Error)
async def error_bd(request: Request, exc: pyodbc.Error):
    logging.getLogger(__name__).exception("Error de base de datos", exc_info=exc)
    return _pagina_error(request, 503, "Base de datos no disponible",
                         "No se pudo consultar BD_Gestion_Horario. Verifica que SQL Server esté en ejecución y revisa config.py.")


def direcciones_locales():
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith("127."))


def main():
    logging.basicConfig(level=logging.INFO)
    sufijo = "" if config.PUERTO == 80 else ":%d" % config.PUERTO
    print("\n  Sistema de horarios · ULEAM")
    print("  Local ......: http://localhost%s/" % sufijo)
    for ip in direcciones_locales():
        print("  En la red ..: http://%s%s/" % (ip, sufijo))
    try:
        import consultas
        faltan = consultas.verificar_tablas()
        print("  Base de datos: conectada." if not faltan else
              "  AVISO: faltan tablas en %s: %s (las crea el programa de ingreso de datos)." % (config.DB_NAME, ", ".join(faltan)))
    except Exception as e:  # noqa: BLE001
        print("  AVISO: no se pudo conectar con SQL Server (%s). Revisa config.py." % e.__class__.__name__)
    print("  (Ctrl+C para detener)\n")
    try:
        uvicorn.run(app, host=config.HOST, port=config.PUERTO, log_level="info")
    except OSError as e:
        print("\n  No se pudo abrir el puerto %d: %s" % (config.PUERTO, e))
        print("  Ejecuta como Administrador y cierra lo que use el puerto 80 (IIS, Apache) o cambia PUERTO en config.py.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
