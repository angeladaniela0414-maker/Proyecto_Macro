import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from db import obtener_conexion

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("Falta SESSION_SECRET en el archivo .env")

app = FastAPI(title="Sistema de Gestión de Horarios")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
    max_age=None,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class DatosLogin(BaseModel):
    correo: str
    contrasena: str

# Todas estas rutas se vinculan a una plantilla y al rol autorizado.
PAGINAS = {
    "estudiante-inicio": ("estudiante-inicio.html", "Estudiante"),
    "estudiante-horario": ("estudiante-horario.html", "Estudiante"),
    "estudiante-consulta": ("estudiante-consulta.html", "Estudiante"),
    "estudiante-salones": ("estudiante-salones.html", "Estudiante"),
    "docente-inicio": ("docente-inicio.html", "Docente"),
    "docente-horario": ("docente-horario.html", "Docente"),
    "docente-consulta": ("docente-consulta.html", "Docente"),
    "docente-salones": ("docente-salones.html", "Docente"),
    "gestion-inicio": ("gestion-inicio.html", "Gestion Academica"),
    "gestion-generar": ("gestion-generar.html", "Gestion Academica"),
    "gestion-consulta": ("gestion-consulta.html", "Gestion Academica"),
    "gestion-docentes": ("gestion-docentes.html", "Gestion Academica"),
    "gestion-estudiantes": ("gestion-estudiantes.html", "Gestion Academica"),
    "gestion-salones": ("gestion-salones.html", "Gestion Academica"),
}
PAGINA_INICIAL = {
    "Estudiante": "/estudiante-inicio",
    "Docente": "/docente-inicio",
    "Gestion Academica": "/gestion-inicio",
}

@app.get("/")
def mostrar_login(request: Request):
    rol = request.session.get("tipo_usuario")
    if request.session.get("usuario_id") is not None and rol in PAGINA_INICIAL:
        return RedirectResponse(PAGINA_INICIAL[rol], status_code=303)
    respuesta = templates.TemplateResponse(
        request=request, name="index.html", context={}
    )
    respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta

@app.post("/api/login")
def iniciar_sesion(datos: DatosLogin, request: Request):
    correo = datos.correo.strip()
    if not correo or not datos.contrasena:
        raise HTTPException(status_code=400, detail="Ingresa el correo y la contraseña.")

    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                u.id,
                u.correoInstitucional,
                u.[contraseña],
                CASE
                    WHEN ga.id IS NOT NULL THEN 'Gestion Academica'
                    WHEN d.id IS NOT NULL THEN 'Docente'
                    WHEN e.id IS NOT NULL THEN 'Estudiante'
                    ELSE NULL
                END AS rol
            FROM dbo.Usuario AS u
            LEFT JOIN dbo.Gestion_Academica AS ga ON ga.id = u.id
            LEFT JOIN dbo.Docente AS d ON d.id = u.id
            LEFT JOIN dbo.Estudiante AS e ON e.id = u.id
            WHERE u.correoInstitucional = ?
            """,
            (correo,),
        )
        usuario = cursor.fetchone()
    finally:
        conexion.close()

    
    if usuario is None:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    id_usuario, correo_bd, contrasena_bd, rol = usuario
    if contrasena_bd is None or datos.contrasena != contrasena_bd:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if rol not in PAGINA_INICIAL:
        raise HTTPException(
            status_code=403,
            detail="La cuenta no está asociada a un registro de Estudiante, Docente o Gestión Académica."
        )

    request.session.clear()
    request.session["usuario_id"] = id_usuario
    request.session["tipo_usuario"] = rol
    request.session["correo"] = correo_bd
    return {"redirect": PAGINA_INICIAL[rol]}

def exigir_perfil(request: Request, rol_requerido: str):
    usuario_id = request.session.get("usuario_id")
    rol_actual = request.session.get("tipo_usuario")
    if usuario_id is None or not rol_actual:
        return RedirectResponse(url="/", status_code=303)
    if rol_actual != rol_requerido:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta interfaz.")
    return None

@app.get("/{pagina}")
def mostrar_pagina(pagina: str, request: Request):
    if pagina not in PAGINAS:
        raise HTTPException(status_code=404, detail="La página solicitada no existe.")
    archivo_html, rol_requerido = PAGINAS[pagina]
    redireccion = exigir_perfil(request, rol_requerido)
    if redireccion is not None:
        return redireccion
    respuesta = templates.TemplateResponse(
        request=request,
        name=archivo_html,
        context={
            "usuario_id": request.session["usuario_id"],
            "tipo_usuario": request.session["tipo_usuario"],
            "correo": request.session.get("correo", ""),
        },
    )

    respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta

@app.post("/api/logout")
def cerrar_sesion(request: Request):
    request.session.clear()
    return {"redirect": "/"}
