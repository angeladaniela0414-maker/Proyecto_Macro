"""Ingreso, salida y solicitud de recuperación de clave."""
import logging

import pyodbc
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import seguridad
from menus import INICIO
from servicios import usuarios

bp = Blueprint("auth", __name__)
log = logging.getLogger(__name__)


def _destino_seguro(ruta):
    return ruta if ruta and ruta.startswith("/") and not ruta.startswith("//") else None


@bp.route("/")
def raiz():
    if "rol" in session:
        return redirect(url_for(INICIO[session["rol"]]))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if "rol" in session:
        return redirect(url_for(INICIO[session["rol"]]))
    error, correo = None, ""
    siguiente = _destino_seguro(request.values.get("siguiente")) or ""
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        clave = request.form.get("clave", "")
        llave = "%s|%s" % (request.remote_addr, correo)
        espera = seguridad.segundos_bloqueado(llave)
        if espera:
            error = "Demasiados intentos fallidos. Intenta de nuevo en %d minutos." % (espera // 60 + 1)
        elif not correo or not clave:
            error = "Ingresa tu correo y tu contraseña."
        else:
            try:
                datos = usuarios.autenticar(correo, clave)
            except ValueError as e:
                error = str(e)
            except pyodbc.Error:
                log.exception("Error de base de datos en el ingreso")
                error = "No se pudo conectar con la base de datos. Avisa al administrador del sistema."
            else:
                if datos:
                    seguridad.limpiar_intentos(llave)
                    session.clear()
                    session.update(datos)
                    session.permanent = bool(request.form.get("recordar"))
                    return redirect(_destino_seguro(siguiente) or url_for(INICIO[datos["rol"]]))
                seguridad.registrar_intento(llave)
                error = "Correo o contraseña incorrectos."
    return render_template("login.html", error=error, correo=correo, siguiente=siguiente)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/recuperar", methods=["POST"])
def recuperar():
    """Registra una solicitud para que Gestión Académica restablezca la clave."""
    correo = request.form.get("correo", "").strip().lower()
    llave = "recuperar|%s" % request.remote_addr
    if seguridad.segundos_bloqueado(llave, maximo=5, ventana=900):
        return jsonify(ok=False, mensaje="Demasiadas solicitudes. Intenta más tarde."), 429
    seguridad.registrar_intento(llave)
    if not usuarios.CORREO_RE.match(correo):
        return jsonify(ok=False, mensaje="Ingresa un correo válido."), 400
    try:
        usuarios.registrar_solicitud_clave(correo)
    except pyodbc.Error:
        log.exception("Error al registrar solicitud de clave")
        return jsonify(ok=False, mensaje="No se pudo registrar la solicitud. Intenta más tarde."), 503
    # Misma respuesta exista o no el correo, para no revelar qué cuentas existen.
    return jsonify(ok=True, mensaje="Si el correo está registrado, Gestión Académica recibió tu solicitud "
                                    "y te entregará una clave temporal.")
