"""Vistas compartidas por todos los roles: perfil, salones y API de horarios."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from seguridad import requiere_rol
from servicios import academico as ac
from servicios import usuarios

bp = Blueprint("comun", __name__)


@bp.route("/perfil", methods=["GET", "POST"])
@requiere_rol()
def perfil():
    if request.method == "POST":
        nueva, repetir = request.form.get("nueva", ""), request.form.get("repetir", "")
        try:
            if nueva != repetir:
                raise ValueError("La confirmación no coincide con la nueva contraseña.")
            usuarios.cambiar_clave(session["rol"], session["uid"], request.form.get("actual", ""), nueva)
            flash("Contraseña actualizada.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("comun.perfil"))
    return render_template("comun/perfil.html")


@bp.route("/salones")
@requiere_rol("estudiante", "docente", "gestion", "admin")
def salones():
    if session["rol"] in ("gestion", "admin"):
        return redirect(url_for("gestor.index"))
    return render_template("comun/salones.html",
                           salones=ac.salones(request.args.get("tipo") or None),
                           tipo=request.args.get("tipo", ""), dias=ac.DIAS)


@bp.route("/api/horario")
@requiere_rol()
def api_horario():
    rol, uid = session["rol"], session["uid"]
    a = request.args
    if a.get("alcance") == "mio":
        if rol == "docente":
            bloques = ac.horario(docente=uid)
        elif rol == "estudiante":
            bloques = ac.horario_estudiante(ac.perfil_estudiante(uid))
        else:
            bloques = []
    else:
        bloques = ac.horario(
            carrera=ac.entero(a.get("carrera")), nivel=ac.entero(a.get("nivel")),
            paralelo=(a.get("paralelo") or "").strip().upper()[:5] or None,
            asignatura=ac.entero(a.get("asignatura")), docente=ac.entero(a.get("docente")),
            periodo=ac.entero(a.get("periodo")))
    return jsonify(bloques=bloques)


@bp.route("/api/salones/libres")
@requiere_rol()
def api_salones_libres():
    try:
        libres = ac.salones_libres(ac.entero(request.args.get("dia")), request.args.get("inicio"),
                                   request.args.get("fin"))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(salones=libres)
