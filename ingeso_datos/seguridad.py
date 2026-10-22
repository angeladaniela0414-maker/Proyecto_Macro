"""Contraseñas, sesiones por rol, CSRF y límite de intentos."""
import hmac
import secrets
import time
from functools import wraps

from flask import abort, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

_PREFIJOS = ("pbkdf2:", "scrypt:")


# --- Contraseñas --------------------------------------------------------------
def hash_clave(clave):
    return generate_password_hash(clave, method="pbkdf2:sha256")


def esta_cifrada(guardada):
    return bool(guardada) and guardada.startswith(_PREFIJOS)


def verificar_clave(guardada, ingresada):
    """Acepta hash (nuevo) o texto plano (datos antiguos, ej. 'admin1234')."""
    if not guardada:
        return False
    if esta_cifrada(guardada):
        return check_password_hash(guardada, ingresada)
    return hmac.compare_digest(guardada.encode("utf-8"), ingresada.encode("utf-8"))


def clave_temporal(largo=10):
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alfabeto) for _ in range(largo))


# --- Sesión y roles -----------------------------------------------------------
def requiere_rol(*roles):
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if "rol" not in session:
                if request.path.startswith(("/api/", "/seccion/")):
                    return jsonify(error="Tu sesión expiró. Vuelve a ingresar."), 401
                return redirect(url_for("auth.login", siguiente=request.path))
            if roles and session["rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


# --- CSRF ---------------------------------------------------------------------
def token_csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def validar_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        esperado = session.get("csrf")
        recibido = request.form.get("csrf") or request.headers.get("X-CSRF-Token")
        if not esperado or not recibido or not hmac.compare_digest(esperado, recibido):
            abort(400)


# --- Límite de intentos (en memoria) -----------------------------------------
_intentos = {}


def segundos_bloqueado(clave, maximo=5, ventana=900):
    reg = _intentos.get(clave)
    if not reg:
        return 0
    n, desde = reg
    restante = ventana - (time.time() - desde)
    if restante <= 0:
        _intentos.pop(clave, None)
        return 0
    return int(restante) if n >= maximo else 0


def registrar_intento(clave, ventana=900):
    n, desde = _intentos.get(clave, (0, time.time()))
    if time.time() - desde > ventana:
        n, desde = 0, time.time()
    _intentos[clave] = (n + 1, desde)


def limpiar_intentos(clave):
    _intentos.pop(clave, None)
