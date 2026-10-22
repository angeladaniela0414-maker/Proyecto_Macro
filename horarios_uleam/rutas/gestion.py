"""Gestión académica: generar y repartir horarios; consultar docentes y estudiantes."""
from typing import List
from urllib.parse import urlencode

import pyodbc
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

import consultas as c
from plantillas import flash, render
from seguridad import requiere, validar_csrf

router = APIRouter(prefix="/gestion")
SOLO_GESTION = Depends(requiere("gestion"))


@router.get("/generar", name="generar")
def generar_form(request: Request, u: dict = SOLO_GESTION):
    cat = c.catalogos()
    periodo = c.entero(request.query_params.get("periodo")) or (c.periodo_activo() or {}).get("id")
    return render(request, "gestion/generar.html", cat=cat, periodo=periodo,
                  generados=c.resumen_generados(periodo) if periodo else [])


@router.post("/generar")
def generar(request: Request, accion: str = Form(""), periodo: int = Form(0), carrera: int = Form(0),
            nivel: int = Form(0), paralelo: List[str] = Form(default=[]), csrf: str = Form(""),
            u: dict = SOLO_GESTION):
    validar_csrf(request, csrf)
    paralelos = sorted({p.strip().upper()[:5] for p in paralelo if p.strip()})
    volver = "/gestion/generar?" + urlencode({"periodo": periodo})
    if not (periodo and carrera and nivel):
        flash(request, "Elige período, carrera y nivel.", "error")
        return RedirectResponse(volver, status_code=303)
    try:
        if accion == "descartar":
            n = c.descartar(periodo, carrera, nivel, paralelos[0] if len(paralelos) == 1 else None)
            flash(request, "Se descartaron %d bloques de horario." % n)
        else:
            n, avisos = c.generar(periodo, carrera, nivel, paralelos)
            flash(request, "Se generaron %d bloques. Ya los ven los docentes y estudiantes de ese nivel." % n)
            for a in avisos[:15]:
                flash(request, a, "aviso")
            if n:
                return RedirectResponse("/horario?" + urlencode(
                    {"periodo": periodo, "carrera": carrera, "nivel": nivel, "paralelo": paralelos[0]}), status_code=303)
    except ValueError as e:
        flash(request, str(e), "error")
    except pyodbc.Error:
        raise
    return RedirectResponse(volver, status_code=303)


@router.get("/docentes", name="docentes")
def docentes(request: Request, u: dict = SOLO_GESTION):
    return render(request, "gestion/docentes.html", docentes=c.docentes())


@router.get("/estudiantes", name="estudiantes")
def estudiantes(request: Request, u: dict = SOLO_GESTION):
    q = request.query_params
    f = dict(carrera=c.entero(q.get("carrera")), nivel=c.entero(q.get("nivel")),
             paralelo=(q.get("paralelo") or "").strip().upper()[:5] or None)
    return render(request, "gestion/estudiantes.html", cat=c.catalogos(), f=f, lista=c.estudiantes(**f))
