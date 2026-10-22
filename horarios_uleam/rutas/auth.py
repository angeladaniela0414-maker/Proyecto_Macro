"""Ingreso y salida."""
import logging

import pyodbc
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

import consultas
import seguridad
from plantillas import render

router = APIRouter()
log = logging.getLogger(__name__)


def _destino(ruta):
    return ruta if ruta and ruta.startswith("/") and not ruta.startswith("//") else "/inicio"


@router.get("/", include_in_schema=False)
def raiz(request: Request):
    return RedirectResponse("/inicio" if seguridad.usuario_actual(request) else "/login", status_code=303)


@router.get("/login", name="login")
def login_form(request: Request, siguiente: str = ""):
    if seguridad.usuario_actual(request):
        return RedirectResponse("/inicio", status_code=303)
    return render(request, "login.html", error=None, usuario_valor="", siguiente=siguiente)


@router.post("/login")
def login(request: Request, usuario: str = Form(""), clave: str = Form(""), recordar: str = Form(""),
          siguiente: str = Form(""), csrf: str = Form("")):
    seguridad.validar_csrf(request, csrf)
    usuario = usuario.strip().lower()
    llave = "%s|%s" % (request.client.host if request.client else "?", usuario)
    error = None
    espera = seguridad.segundos_bloqueado(llave)
    if espera:
        error = "Demasiados intentos fallidos. Intenta de nuevo en %d minutos." % (espera // 60 + 1)
    elif not usuario or not clave:
        error = "Ingresa tu usuario y tu contraseña."
    else:
        try:
            cuenta = consultas.datos_de_acceso(usuario)
        except pyodbc.Error:
            log.exception("Error de base de datos en el ingreso")
            cuenta, error = None, "No se pudo conectar con la base de datos. Avisa al administrador del sistema."
        if not error:
            if not cuenta or not seguridad.verificar_clave(cuenta["clave"], clave):
                seguridad.registrar_fallo(llave)
                error = "Usuario o contraseña incorrectos."
            elif cuenta["rol"] is None:
                error = "Tu usuario no tiene un rol asignado. Contacta a Gestión Académica."
            elif not cuenta["activo"]:
                error = "Tu cuenta está inactiva. Contacta a Gestión Académica."
            else:
                seguridad.limpiar_fallos(llave)
                seguridad.iniciar_sesion(request, {
                    "rol": cuenta["rol"], "uid": cuenta["id"], "correo": cuenta["correo"],
                    "nombre": cuenta["nombre"], "apellido": cuenta["apellido"]}, bool(recordar))
                return RedirectResponse(_destino(siguiente), status_code=303)
    return render(request, "login.html", error=error, usuario_valor=usuario, siguiente=siguiente)


@router.post("/logout")
def logout(request: Request, csrf: str = Form("")):
    seguridad.validar_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
