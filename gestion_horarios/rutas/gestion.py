"""Portal de Gestión Académica (y Administrador)."""
import csv
import io

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, session, url_for

from seguridad import requiere_rol
from servicios import academico as ac
from servicios import usuarios

bp = Blueprint("gestion", __name__, url_prefix="/gestion")
SOLO = requiere_rol("gestion", "admin")


def _volver(defecto):
    destino = request.form.get("volver")
    return redirect(url_for(destino if destino in ("gestion.docentes", "gestion.estudiantes") else defecto))


def _con_error(accion, ok, defecto):
    try:
        accion()
        flash(ok, "ok")
    except ValueError as e:
        flash(str(e), "error")
    return _volver(defecto)


@bp.route("/")
@SOLO
def inicio():
    perfil = ac.perfil_gestion(session["uid"]) if session["rol"] == "gestion" else None
    return render_template("gestion/inicio.html", resumen=ac.resumen_gestion(), perfil=perfil,
                           periodo=ac.periodo_activo())


@bp.route("/generacion-horarios")
@SOLO
def generacion():
    # Módulo reservado: la generación de horarios se implementará en una siguiente etapa.
    return render_template("gestion/generacion_horarios.html")


# ---- Salones ----
@bp.route("/salones", methods=["GET", "POST"])
@SOLO
def salones():
    if request.method == "POST":
        f = request.form
        return _con_error(lambda: ac.crear_salon(f.get("numero"), f.get("nombre"), f.get("capacidad"), f.get("tipo")),
                          "Salón creado.", "gestion.salones")
    return render_template("gestion/salones.html", salones=ac.salones(), dias=ac.DIAS)


@bp.route("/salones/<int:id_salon>/estado", methods=["POST"])
@SOLO
def salon_estado(id_salon):
    return _con_error(lambda: ac.estado_salon(id_salon, request.form.get("estado")),
                      "Estado del salón actualizado.", "gestion.salones")


@bp.route("/salones/<int:id_salon>/eliminar", methods=["POST"])
@SOLO
def salon_eliminar(id_salon):
    return _con_error(lambda: ac.eliminar_salon(id_salon), "Salón eliminado.", "gestion.salones")


# ---- Docentes ----
@bp.route("/docentes", methods=["GET", "POST"])
@SOLO
def docentes():
    if request.method == "POST":
        f = request.form
        return _con_error(lambda: usuarios.crear_docente(f.get("correo"), f.get("clave"), f.get("nombre"),
                          f.get("apellido"), f.get("cedula"), f.get("especialidad"), f.get("nivel")),
                          "Docente creado.", "gestion.docentes")
    return render_template("gestion/docentes.html", docentes=ac.docentes())


@bp.route("/docentes/<int:id_docente>/estado", methods=["POST"])
@SOLO
def docente_estado(id_docente):
    activo = request.form.get("activo") == "1"
    ac.estado_docente(id_docente, activo)
    flash("Docente activado." if activo else "Docente desactivado.", "ok")
    return redirect(url_for("gestion.docentes"))


# ---- Estudiantes ----
@bp.route("/estudiantes", methods=["GET", "POST"])
@SOLO
def estudiantes():
    if request.method == "POST":
        f = request.form
        return _con_error(lambda: usuarios.crear_estudiante(f.get("correo"), f.get("clave"), f.get("nombre"),
                          f.get("apellido"), f.get("carrera"), f.get("nivel"), f.get("curso")),
                          "Estudiante creado.", "gestion.estudiantes")
    carrera, nivel, curso = request.args.get("carrera") or None, ac.entero(request.args.get("nivel")), \
        (request.args.get("curso") or "").strip() or None
    return render_template("gestion/estudiantes.html", estudiantes=ac.estudiantes(carrera, nivel, curso),
                           cat=ac.catalogos(), f={"carrera": carrera or "", "nivel": nivel or "", "curso": curso or ""})


@bp.route("/usuarios/<int:uid>/restablecer", methods=["POST"])
@SOLO
def restablecer(uid):
    correo = usuarios.correo_de(uid)
    if not correo:
        abort(404)
    flash("%s::%s" % (correo, usuarios.restablecer_clave(correo)), "clave")
    return _volver("gestion.docentes")


# ---- Asignaturas ----
@bp.route("/asignaturas", methods=["GET", "POST"])
@SOLO
def asignaturas():
    if request.method == "POST":
        f = request.form
        return _con_error(lambda: ac.crear_asignatura(f.get("codigo"), f.get("nombre"), f.get("carrera"),
                          f.get("nivel"), f.get("horas")), "Asignatura creada.", "gestion.asignaturas")
    carrera, nivel = ac.entero(request.args.get("carrera")), ac.entero(request.args.get("nivel"))
    return render_template("gestion/asignaturas.html", asignaturas=ac.asignaturas(carrera, nivel),
                           cat=ac.catalogos(), f={"carrera": carrera or "", "nivel": nivel or ""})


# ---- Solicitudes de clave ----
@bp.route("/solicitudes-clave")
@SOLO
def solicitudes():
    return render_template("gestion/solicitudes_clave.html", solicitudes=ac.solicitudes_clave())


@bp.route("/solicitudes-clave/<int:id_sol>/atender", methods=["POST"])
@SOLO
def atender(id_sol):
    s = ac.solicitud(id_sol)
    if not s or s["estado"] != "Pendiente":
        flash("La solicitud ya fue atendida.", "error")
    else:
        try:
            flash("%s::%s" % (s["correo"], usuarios.restablecer_clave(s["correo"])), "clave")
            ac.marcar_solicitud(id_sol, "Atendida")
        except ValueError as e:
            ac.marcar_solicitud(id_sol, "Rechazada")
            flash(str(e), "error")
    return redirect(url_for("gestion.solicitudes"))


# ---- Reportes ----
@bp.route("/reportes")
@SOLO
def reportes():
    return render_template("gestion/reportes.html", reportes={k: v[0] for k, v in ac.REPORTES.items()})


@bp.route("/reportes/<tipo>.csv")
@SOLO
def reporte_csv(tipo):
    if tipo not in ac.REPORTES:
        abort(404)
    from conexion_db import transaccion
    with transaccion() as cur:
        cur.execute(ac.REPORTES[tipo][1])
        encabezados = [c[0] for c in cur.description]
        filas = [list(f) for f in cur.fetchall()]
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return Response("\ufeff" + salida.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=%s.csv" % tipo})
