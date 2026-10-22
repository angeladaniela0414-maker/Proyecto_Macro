"""Portal del estudiante: organizador de horario, registro, tutorías y comprobantes."""
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from seguridad import requiere_rol
from servicios import academico as ac

bp = Blueprint("estudiante", __name__, url_prefix="/estudiante")
SOLO = requiere_rol("estudiante")


def _perfil():
    p = ac.perfil_estudiante(session["uid"])
    if not p:
        abort(403)
    return p


@bp.route("/")
@SOLO
def inicio():
    perfil = _perfil()
    bloques = ac.horario_estudiante(perfil)
    hoy = datetime.now().isoweekday()
    return render_template(
        "estudiante/inicio.html", perfil=perfil, periodo=ac.periodo_activo(),
        registro=ac.registro_activo(perfil["id"]), asignaturas=ac.resumen_asignaturas(bloques),
        clases_hoy=[b for b in bloques if b["dia"] == hoy], tutorias=ac.tutorias_solicitadas(perfil["id"]),
        libres=sum(1 for s in ac.salones(estado="Disponible") if not s["ocupado"]))


@bp.route("/horario")
@SOLO
def horario():
    perfil = _perfil()
    sel = {"carrera": perfil["idCarrera"], "nivel": perfil["nivel"], "paralelo": ac.paralelo_efectivo(perfil)}
    return render_template("estudiante/horario.html", perfil=perfil, cat=ac.catalogos(), sel=sel,
                           periodo=ac.periodo_activo())


@bp.route("/registro", methods=["GET", "POST"])
@SOLO
def registro():
    perfil = _perfil()
    if request.method == "POST":
        try:
            codigo = ac.registrar_horario(perfil, (request.form.get("paralelo") or "").strip().upper())
            flash("Horario registrado. Código de comprobante: %s." % codigo, "ok")
            return redirect(url_for("estudiante.comprobantes"))
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("estudiante.registro"))
    return render_template("estudiante/registro.html", perfil=perfil, periodo=ac.periodo_activo(),
                           registro=ac.registro_activo(perfil["id"]),
                           paralelos=ac.paralelos_disponibles(perfil["carrera"], perfil["nivel"]),
                           actual=ac.paralelo_efectivo(perfil))


@bp.route("/tutorias")
@SOLO
def tutorias():
    perfil = _perfil()
    return render_template("estudiante/tutorias.html", perfil=perfil,
                           disponibles=ac.tutorias_para_estudiante(perfil),
                           solicitadas=ac.tutorias_solicitadas(perfil["id"]))


@bp.route("/tutorias/<int:id_tut>/solicitar", methods=["POST"])
@SOLO
def solicitar(id_tut):
    try:
        ac.solicitar_tutoria(session["uid"], id_tut)
        flash("Tutoría solicitada.", "ok")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("estudiante.tutorias"))


@bp.route("/tutorias/<int:id_tut>/cancelar", methods=["POST"])
@SOLO
def cancelar(id_tut):
    ac.cancelar_solicitud(session["uid"], id_tut)
    flash("Solicitud cancelada.", "ok")
    return redirect(url_for("estudiante.tutorias"))


@bp.route("/comprobantes")
@SOLO
def comprobantes():
    return render_template("estudiante/comprobantes.html", registros=ac.registros_estudiante(session["uid"]))


@bp.route("/comprobantes/<int:rid>")
@SOLO
def comprobante(rid):
    perfil = _perfil()
    reg = ac.registro_detalle(perfil["id"], rid)
    if not reg:
        abort(404)
    bloques = ac.horario(carrera_nombre=perfil["carrera"], nivel=reg["nivel"], paralelo=reg["paralelo"],
                         periodo=reg["idPeriodo"])
    return render_template("estudiante/comprobante.html", perfil=perfil, reg=reg,
                           asignaturas=ac.resumen_asignaturas(bloques), fijos={"carrera": perfil["idCarrera"],
                           "nivel": reg["nivel"], "paralelo": reg["paralelo"], "periodo": reg["idPeriodo"]})
