"""Portal del docente: horarios por nivel/asignatura/paralelo, tutorías y estudiantes."""
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from seguridad import requiere_rol
from servicios import academico as ac

bp = Blueprint("docente", __name__, url_prefix="/docente")
SOLO = requiere_rol("docente")


@bp.route("/")
@SOLO
def inicio():
    uid = session["uid"]
    bloques = ac.horario(docente=uid)
    hoy = datetime.now().isoweekday()
    tutorias = [t for t in ac.tutorias_docente(uid)
                if t["estado"] == "Programada" and t["fecha"] >= datetime.now().strftime("%Y-%m-%d")]
    return render_template(
        "docente/inicio.html", periodo=ac.periodo_activo(), asignaturas=ac.resumen_asignaturas(bloques),
        horas=ac.horas_semanales(bloques), clases_hoy=[b for b in bloques if b["dia"] == hoy],
        tutorias=tutorias, total_estudiantes=len({e["id"] for e in ac.estudiantes_de_docente(uid)}))


@bp.route("/horario")
@SOLO
def horario():
    return render_template("docente/horario.html", periodo=ac.periodo_activo())


@bp.route("/horarios")
@SOLO
def horarios():
    return render_template("docente/horarios.html", cat=ac.catalogos())


@bp.route("/tutorias", methods=["GET", "POST"])
@SOLO
def tutorias():
    uid = session["uid"]
    if request.method == "POST":
        try:
            ac.crear_tutoria(uid, request.form)
            flash("Tutoría programada.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("docente.tutorias"))
    return render_template("docente/tutorias.html", tutorias=ac.tutorias_docente(uid),
                           asignaturas=ac.asignaturas_docente(uid),
                           salones=[s for s in ac.salones(estado="Disponible")],
                           hoy=datetime.now().strftime("%Y-%m-%d"))


@bp.route("/tutorias/<int:id_tut>/cancelar", methods=["POST"])
@SOLO
def cancelar(id_tut):
    try:
        ac.cancelar_tutoria(session["uid"], id_tut)
        flash("Tutoría cancelada. Se avisó el cambio en las solicitudes de los estudiantes.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("docente.tutorias"))


@bp.route("/tutorias/<int:id_tut>/solicitantes")
@SOLO
def solicitantes(id_tut):
    return jsonify(estudiantes=ac.solicitantes_tutoria(session["uid"], id_tut))


@bp.route("/estudiantes")
@SOLO
def estudiantes():
    asig = ac.entero(request.args.get("asignatura"))
    return render_template("docente/estudiantes.html", estudiantes=ac.estudiantes_de_docente(session["uid"], asig),
                           asignaturas=ac.asignaturas_docente(session["uid"]), asig=asig)
