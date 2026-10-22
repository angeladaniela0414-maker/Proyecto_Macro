"""Sesión por rol, contraseñas (solo lectura), CSRF y límite de intentos."""
import hmac
import secrets
import time

from fastapi import HTTPException, Request

import config


class IrALogin(Exception):
    def __init__(self, destino=""):
        self.destino = destino


# --- Contraseñas: este sistema nunca las escribe --------------------------------
def verificar_clave(guardada, ingresada):
    """Acepta texto plano o hash (pbkdf2/scrypt de Werkzeug), según cómo las guarde el programa de datos."""
    if not guardada:
        return False
    if guardada.startswith(("pbkdf2:", "scrypt:")):
        from werkzeug.security import check_password_hash
        return check_password_hash(guardada, ingresada)
    return hmac.compare_digest(guardada.encode("utf-8"), ingresada.encode("utf-8"))


# --- Sesión -------------------------------------------------------------------
def iniciar_sesion(request: Request, datos: dict, recordar: bool):
    request.session.clear()
    request.session.update(datos)
    vida = config.DIAS_RECORDAR * 86400 if recordar else config.HORAS_SESION * 3600
    request.session["exp"] = time.time() + vida


def usuario_actual(request: Request):
    s = request.session
    if "rol" not in s:
        return None
    if s.get("exp", 0) < time.time():
        s.clear()
        return None
    return {k: s.get(k) for k in ("rol", "uid", "correo", "nombre", "apellido")}


def requiere(*roles):
    """Dependencia de FastAPI: exige sesión y, opcionalmente, uno de los roles."""
    def dependencia(request: Request):
        u = usuario_actual(request)
        if not u:
            raise IrALogin(request.url.path)
        if roles and u["rol"] not in roles:
            raise HTTPException(status_code=403)
        return u
    return dependencia


# --- CSRF ---------------------------------------------------------------------
def token_csrf(request: Request):
    if "csrf" not in request.session:
        request.session["csrf"] = secrets.token_hex(16)
    return request.session["csrf"]


def validar_csrf(request: Request, recibido: str):
    esperado = request.session.get("csrf")
    if not esperado or not recibido or not hmac.compare_digest(esperado, recibido):
        raise HTTPException(status_code=400)


# --- Límite de intentos (en memoria) ---------------------------------------------
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


def registrar_fallo(clave, ventana=900):
    n, desde = _intentos.get(clave, (0, time.time()))
    if time.time() - desde > ventana:
        n, desde = 0, time.time()
    _intentos[clave] = (n + 1, desde)


def limpiar_fallos(clave):
    _intentos.pop(clave, None)
