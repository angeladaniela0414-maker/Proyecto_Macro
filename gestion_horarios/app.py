"""Portal académico ULEAM · Gestión de horarios.

Ejecutar:  python app.py      (el puerto 80 requiere permisos de administrador)
"""
import logging
import socket
from datetime import datetime, timedelta

import pyodbc
from flask import Flask, jsonify, render_template, request, session
from markupsafe import Markup

import config
from menus import ETIQUETAS, MENUS
from seguridad import token_csrf, validar_csrf

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def crear_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        MAX_CONTENT_LENGTH=1024 * 1024,
        JSON_AS_ASCII=False,
    )

    from rutas import auth, comun, docente, estudiante, gestion
    for modulo in (auth, comun, estudiante, docente, gestion):
        app.register_blueprint(modulo.bp)

    app.before_request(validar_csrf)

    @app.after_request
    def cabeceras(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        if "rol" in session:
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.context_processor
    def contexto():
        rol = session.get("rol")
        nombre = ("%s %s" % (session.get("nombre", ""), session.get("apellido", ""))).strip()
        return dict(
            rol=rol, menu=MENUS.get(rol, []), etiqueta_rol=ETIQUETAS.get(rol, ""),
            usuario_nombre=nombre, usuario_inicial=(nombre[:1] or "U").upper(),
            csrf_token=token_csrf,
            csrf_campo=lambda: Markup('<input type="hidden" name="csrf" value="%s">' % token_csrf()),
        )

    @app.template_filter("fecha_es")
    def fecha_es(v, con_hora=False):
        if not v:
            return ""
        try:
            d = datetime.strptime(v[:10], "%Y-%m-%d")
        except ValueError:
            return v
        s = d.strftime("%d/%m/%Y")
        return s + " " + v[11:16] if con_hora and len(v) > 10 else s

    @app.template_filter("fecha_larga")
    def fecha_larga(v):
        try:
            d = datetime.strptime(v[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return v or ""
        if d.date() == datetime.now().date():
            return "Hoy"
        return "%s %d de %s" % (DIAS_SEMANA[d.weekday()].capitalize(), d.day, MESES[d.month - 1])

    @app.template_filter("dia_nombre")
    def dia_nombre(n):
        return (["", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"] + [""] * 5)[int(n)]

    def _error(codigo, titulo, detalle):
        if request.path.startswith("/api/"):
            return jsonify(error=detalle), codigo
        return render_template("error.html", codigo=codigo, titulo=titulo, detalle=detalle), codigo

    @app.errorhandler(pyodbc.Error)
    def error_bd(e):
        app.logger.exception("Error de base de datos")
        return _error(503, "Base de datos no disponible",
                      "No se pudo consultar BD_Gestion_Horario. Verifica que SQL Server esté en ejecución "
                      "y revisa la conexión en config.py.")

    @app.errorhandler(400)
    def e400(e):
        return _error(400, "Solicitud no válida", "La sesión del formulario expiró. Recarga la página e inténtalo de nuevo.")

    @app.errorhandler(403)
    def e403(e):
        return _error(403, "Sin permiso", "Tu rol no tiene acceso a esta sección.")

    @app.errorhandler(404)
    def e404(e):
        return _error(404, "Página no encontrada", "La dirección no existe o fue movida.")

    return app


app = crear_app()


def direcciones_locales():
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))  # no envía datos: solo elige la tarjeta de red activa
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith("127."))


def main():
    logging.basicConfig(level=logging.INFO)
    puerto = config.PUERTO
    sufijo = "" if puerto == 80 else ":%d" % puerto
    print("\n  Portal ULEAM · Gestión de horarios")
    print("  Local ......: http://localhost%s/" % sufijo)
    for ip in direcciones_locales():
        print("  En la red ..: http://%s%s/" % (ip, sufijo))
    print("  (Ctrl+C para detener)\n")
    try:
        try:
            from waitress import serve
            serve(app, host=config.HOST, port=puerto, threads=8)
        except ImportError:
            app.run(host=config.HOST, port=puerto, threaded=True)
    except (PermissionError, OSError) as e:
        print("\n  No se pudo abrir el puerto %d: %s" % (puerto, e))
        print("  - Ejecuta la terminal como Administrador.")
        print("  - Cierra lo que use el puerto 80 (IIS / 'World Wide Web Publishing', Apache, otro servidor).")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
