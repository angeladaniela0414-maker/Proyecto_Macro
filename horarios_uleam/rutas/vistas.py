"""Pantallas de consulta para los tres roles: inicio, horarios (con filtros y PDF) y salones."""
from datetime import datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

import consultas as c
import pdf
from plantillas import render
from seguridad import requiere

router = APIRouter()
CUALQUIERA = Depends(requiere())


def _perfil_est(u):
    return c.perfil_estudiante(u["uid"])


def _bloques_propios(u):
    """Horario que le corresponde a la persona que inició sesión."""
    if u["rol"] == "docente":
        return c.horario(docente=u["uid"])
    if u["rol"] == "estudiante":
        p = _perfil_est(u)
        if p and p["idCarrera"]:
            return c.horario(carrera=p["idCarrera"], nivel=p["nivel"], paralelo=c.letra_paralelo(p["curso"]))
    return []


# ------------------------------------------------------------------ inicio
@router.get("/inicio", name="inicio")
def inicio(request: Request, u: dict = CUALQUIERA):
    periodo = c.periodo_activo()
    datos = dict(periodo=periodo, hoy=datetime.now().isoweekday(), dias=c.DIAS)
    if u["rol"] == "gestion":
        if periodo:
            datos.update(resumen=c.resumen_gestion(periodo["id"]), conflictos=c.conflictos(periodo["id"]))
        else:
            datos.update(resumen=None, conflictos=[])
    else:
        bloques = _bloques_propios(u)
        datos.update(perfil=_perfil_est(u) if u["rol"] == "estudiante" else None, asignaturas=c.resumen_asignaturas(bloques),
                     horas=c.horas_semanales(bloques), clases_hoy=[b for b in bloques if b["dia"] == datos["hoy"]])
    return render(request, "inicio.html", **datos)


# ------------------------------------------------------------------ horarios
CAMPOS = ("periodo", "carrera", "nivel", "asignatura", "docente", "salon")


def _filtros(request: Request, u: dict):
    q = request.query_params
    f = {k: c.entero(q.get(k)) for k in CAMPOS}
    f["paralelo"] = (q.get("paralelo") or "").strip().upper()[:5] or None
    # Estudiante/docente: sin parámetros (o «mio») = su propio horario
    if u["rol"] in ("estudiante", "docente") and (q.get("mio") or not q):
        if u["rol"] == "docente":
            f["docente"] = u["uid"]
        else:
            p = _perfil_est(u)
            if p:
                f.update(carrera=p["idCarrera"], nivel=p["nivel"], paralelo=c.letra_paralelo(p["curso"]))
    return f


def _hay_filtro(f):
    return any(f[k] for k in ("carrera", "nivel", "paralelo", "asignatura", "docente", "salon"))


def _descripcion(f, cat):
    nombre = lambda lista, i, col="nombre": next((x[col] for x in lista if x["id"] == i), None)  # noqa: E731
    partes = []
    per = nombre(cat["periodos"], f["periodo"]) if f["periodo"] else None
    partes.append("Período %s" % (per or "activo"))
    if f["carrera"]: partes.append(nombre(cat["carreras"], f["carrera"]) or "")
    if f["nivel"]: partes.append("Nivel %s" % f["nivel"])
    if f["paralelo"]: partes.append("Paralelo %s" % f["paralelo"])
    if f["asignatura"]: partes.append(nombre(cat["asignaturas"], f["asignatura"]) or "")
    if f["docente"]: partes.append("Docente: %s" % (nombre(cat["docentes"], f["docente"]) or ""))
    if f["salon"]: partes.append("Salón: %s" % (nombre(cat["salones"], f["salon"]) or ""))
    return " · ".join(p for p in partes if p)


@router.get("/horario", name="horario")
def horario(request: Request, u: dict = CUALQUIERA):
    cat, f = c.catalogos(), _filtros(request, u)
    bloques = c.horario(**f) if _hay_filtro(f) else None
    franjas, celdas = c.matriz(bloques) if bloques else ([], {})
    grupos = {(b["idCarrera"], b["nivel"], b["paralelo"]) for b in bloques or []}
    pdf_url = "/horario.pdf?" + urlencode({k: v for k, v in f.items() if v})
    return render(request, "horario.html", cat=cat, f=f, bloques=bloques, franjas=franjas, celdas=celdas,
                  dias=c.DIAS, hoy=datetime.now().isoweekday(), varios_grupos=len(grupos) > 1, pdf_url=pdf_url,
                  descripcion=_descripcion(f, cat),
                  conflictos=c.conflictos(f["periodo"] or (c.periodo_activo() or {}).get("id", 0))
                  if u["rol"] == "gestion" and bloques else [])


@router.get("/horario.pdf", name="horario_pdf")
def horario_pdf(request: Request, u: dict = CUALQUIERA):
    cat, f = c.catalogos(), _filtros(request, u)
    if not _hay_filtro(f):
        return Response("Elige al menos un filtro para generar el PDF.", status_code=400)
    bloques = c.horario(**f)
    grupos = {(b["idCarrera"], b["nivel"], b["paralelo"]) for b in bloques}
    contenido = pdf.horario_pdf(bloques, "Horario semanal · ULEAM", _descripcion(f, cat), mostrar_grupo=len(grupos) > 1)
    return Response(contenido, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="horario.pdf"'})


# ------------------------------------------------------------------ salones
@router.get("/salones", name="salones")
def salones(request: Request, u: dict = CUALQUIERA):
    q = request.query_params
    tipo = q.get("tipo") or None
    libres, error = None, None
    if q.get("dia"):
        try:
            libres = c.salones_libres(c.entero(q.get("dia")), q.get("inicio"), q.get("fin"))
        except ValueError as e:
            error = str(e)
    return render(request, "salones.html", lista=c.salones(tipo), tipo=tipo or "", dias=c.DIAS, libres=libres,
                  error=error, busqueda=dict(dia=c.entero(q.get("dia"), 1), inicio=q.get("inicio") or "08:00",
                                             fin=q.get("fin") or "10:00"))
