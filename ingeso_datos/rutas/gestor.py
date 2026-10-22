"""Panel de Gestión Académica (CRUD) conectado a BD_Gestion_Horario.

Mantiene las mismas rutas /api/... que usa la interfaz del gestor; solo cambia la base de datos.
"""
import csv
import io
import math
import unicodedata
from datetime import date, timedelta

import pyodbc
from flask import Blueprint, Response, abort, jsonify, render_template, request, session

from conexion_db import consultar, consultar_uno, ejecutar, insertar, transaccion
from seguridad import requiere_rol
from servicios import usuarios

bp = Blueprint("gestor", __name__)
SOLO = requiere_rol("gestion", "admin")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
HORA_APERTURA, HORA_CIERRE = 7, 21
SECCIONES = {"inicio", "estudiantes", "docentes", "aulas", "laboratorios", "generacion_horarios",
             "asignaturas", "claves", "exportar_reportes"}
ESTADOS_SALON = {"Disponible", "Ocupado", "Mantenimiento"}
TIPOS_SALON = {"Aula", "Laboratorio", "Auditorio"}
CARRERA_DEFECTO = "Ingeniería en Software"
NOMBRE_DIA = "CASE h.dia WHEN 1 THEN N'Lunes' WHEN 2 THEN N'Martes' WHEN 3 THEN N'Miércoles' " \
             "WHEN 4 THEN N'Jueves' ELSE N'Viernes' END"


# ------------------------------------------------------------------ utilidades
def error(msg, codigo=400):
    return jsonify(error=msg), codigo


@bp.errorhandler(ValueError)
def valor_invalido(e):
    return error(str(e))


def faltantes(datos, campos):
    return [c for c in campos if datos.get(c) in (None, "")]


def entero(valor, nombre, minimo=None, maximo=None):
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValueError("%s debe ser un número entero" % nombre)
    if (minimo is not None and n < minimo) or (maximo is not None and n > maximo):
        raise ValueError("%s debe estar entre %s y %s" % (nombre, minimo, maximo))
    return n


def cedula_valida(valor):
    c = str(valor or "").strip()
    if not (c.isdigit() and len(c) == 10):
        raise ValueError("La cédula debe tener 10 dígitos numéricos")
    return c


def _sin_tildes(texto):
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


def generar_correo(nombre, apellido, sufijo):
    base = "%s.%s" % (_sin_tildes(nombre.split()[0]), _sin_tildes(apellido.split()[0]))
    correo = "%s@%s" % (base, usuarios.DOMINIO)
    if consultar("SELECT 1 AS x FROM Usuario WHERE correoInstitucional = ?", (correo,)):
        correo = "%s%s@%s" % (base, sufijo, usuarios.DOMINIO)
    return correo


def carrera(nombre):
    """Devuelve (id, nombre) de la carrera; la crea si no existe."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("Indica la carrera")
    f = consultar_uno("SELECT id, nombre FROM Carrera WHERE nombre = ?", (nombre,))
    if f:
        return f["id"], f["nombre"]
    fac = consultar_uno("SELECT TOP 1 id FROM Facultad ORDER BY id")
    fid = fac["id"] if fac else insertar(
        "INSERT INTO Facultad (numeroDeFacultad, nombre) OUTPUT INSERTED.id VALUES (1, N'Facultad de Ciencias Informáticas')")
    cod = consultar_uno("SELECT ISNULL(MAX(codigo), 100) + 1 AS c FROM Carrera")["c"]
    return insertar("INSERT INTO Carrera (codigo, nombre, idFacultad) OUTPUT INSERTED.id VALUES (?, ?, ?)",
                    (cod, nombre, fid)), nombre


def periodo_id(nombre):
    """Id del período por nombre; lo crea si no existe (activo solo si no hay otro activo)."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("Indica el período")
    f = consultar_uno("SELECT id FROM PeriodoAcademico WHERE nombre = ?", (nombre,))
    if f:
        return f["id"]
    hay_activo = consultar_uno("SELECT COUNT(*) AS n FROM PeriodoAcademico WHERE activo = 1")["n"] > 0
    return insertar("INSERT INTO PeriodoAcademico (nombre, fechaInicio, fechaFin, activo) "
                    "OUTPUT INSERTED.id VALUES (?, ?, ?, ?)",
                    (nombre, date.today(), date.today() + timedelta(days=120), 0 if hay_activo else 1))


def _nombres_carreras():
    return [c["nombre"] for c in consultar("SELECT nombre FROM Carrera ORDER BY nombre")]


def _periodo_activo():
    f = consultar_uno("SELECT TOP 1 nombre FROM PeriodoAcademico WHERE activo = 1 ORDER BY id DESC")
    return f["nombre"] if f else None


# ------------------------------------------------------------------ páginas
@bp.route("/index")
@SOLO
def index():
    nombre = ("%s %s" % (session.get("nombre", ""), session.get("apellido", ""))).strip()
    return render_template("gestor/index.html", usuario=nombre or session.get("correo"),
                           rol="Administrador" if session["rol"] == "admin" else "Gestión académica")


@bp.route("/seccion/<nombre>")
@SOLO
def seccion(nombre):
    if nombre not in SECCIONES:
        abort(404)
    return render_template("gestor/secciones/%s.html" % nombre, dias=DIAS,
                           carreras=_nombres_carreras() or [CARRERA_DEFECTO], periodo=_periodo_activo())


@bp.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


# ------------------------------------------------------------------ docentes
@bp.get("/api/docentes")
@SOLO
def docentes_listar():
    return jsonify(consultar(
        "SELECT d.id, d.cedula, d.nombre, d.apellido, d.especialidad, d.asignatura, d.nivel, "
        "CAST(d.estado AS INT) AS estado, u.correoInstitucional AS correo "
        "FROM Docente d JOIN Usuario u ON u.id = d.id ORDER BY d.apellido, d.nombre"))


@bp.post("/api/docentes")
@SOLO
def docentes_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["cedula", "nombre", "apellido", "asignatura", "nivel"]):
        return error("Cédula, nombre, apellido, asignatura y nivel son obligatorios")
    cedula = cedula_valida(d["cedula"])
    nivel = entero(d["nivel"], "El nivel", 1, 10)
    if consultar("SELECT 1 AS x FROM Docente WHERE cedula = ?", (cedula,)):
        return error("Ya existe un docente con esa cédula", 409)
    nombre, apellido = d["nombre"].strip(), d["apellido"].strip()
    correo = generar_correo(nombre, apellido, cedula[-4:])
    nuevo = usuarios.crear_docente(correo, cedula, nombre, apellido, cedula,
                                   (d.get("especialidad") or "").strip(), nivel, d["asignatura"].strip())
    return jsonify(id=nuevo, correo=correo), 201


@bp.put("/api/docentes/<int:id_>/estado")
@SOLO
def docentes_estado(id_):
    ejecutar("UPDATE Docente SET estado = CASE WHEN estado = 1 THEN 0 ELSE 1 END WHERE id = ?", (id_,))
    return jsonify(ok=True)


@bp.delete("/api/docentes/<int:id_>")
@SOLO
def docentes_eliminar(id_):
    if (consultar("SELECT TOP 1 1 AS x FROM Asignatura WHERE idDocente = ?", (id_,))
            or consultar("SELECT TOP 1 1 AS x FROM Horario WHERE idDocente = ?", (id_,))
            or consultar("SELECT TOP 1 1 AS x FROM Tutoria WHERE idDocente = ?", (id_,))):
        return error("El docente tiene asignaturas, horarios o tutorías asignados; desactívalo en su lugar", 409)
    with transaccion() as cur:
        cur.execute("DELETE FROM Docente WHERE id = ?", (id_,))
        cur.execute("DELETE FROM Usuario WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ estudiantes
@bp.get("/api/estudiantes")
@SOLO
def estudiantes_listar():
    return jsonify(consultar(
        "SELECT id, cedula, codigoRegistro AS codigo_registro, nombre, apellido, "
        "correoInstitucional AS correo_institucional, curso, carrera, nivel, asignatura "
        "FROM Estudiante ORDER BY apellido, nombre"))


@bp.post("/api/estudiantes")
@SOLO
def estudiantes_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["cedula", "codigo_registro", "nombre", "apellido", "curso", "carrera", "nivel"]):
        return error("Cédula, código de registro, nombre, apellido, curso, carrera y nivel son obligatorios")
    cedula = cedula_valida(d["cedula"])
    codigo = entero(d["codigo_registro"], "El código de registro", 1)
    nivel = entero(d["nivel"], "El nivel", 1, 10)
    if consultar("SELECT 1 AS x FROM Estudiante WHERE cedula = ?", (cedula,)):
        return error("Ya existe un estudiante con esa cédula", 409)
    if consultar("SELECT 1 AS x FROM Estudiante WHERE codigoRegistro = ?", (codigo,)):
        return error("Ya existe un estudiante con ese código de registro", 409)
    nombre, apellido = d["nombre"].strip(), d["apellido"].strip()
    correo = generar_correo(nombre, apellido, codigo)
    _, nombre_carrera = carrera(d["carrera"])
    nuevo = usuarios.crear_estudiante(correo, cedula, nombre, apellido, nombre_carrera, nivel,
                                      d["curso"].strip(), cedula=cedula, codigo=codigo,
                                      asignatura=d.get("asignatura"))
    return jsonify(id=nuevo, correo_institucional=correo), 201


@bp.delete("/api/estudiantes/<int:id_>")
@SOLO
def estudiantes_eliminar(id_):
    with transaccion() as cur:
        cur.execute("DELETE FROM TutoriaSolicitud WHERE idEstudiante = ?", (id_,))
        cur.execute("DELETE FROM Registro WHERE idEstudiante = ?", (id_,))
        cur.execute("DELETE FROM Estudiante WHERE id = ?", (id_,))
        cur.execute("DELETE FROM Usuario WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ asignaturas
@bp.get("/api/asignaturas")
@SOLO
def asignaturas_listar():
    sql = ("SELECT a.id, a.codigo, a.nombre, a.nivel, c.nombre AS carrera, a.horasSemanales AS horas_semanales, "
           "a.idDocente AS docente_id FROM Asignatura a JOIN Carrera c ON c.id = a.idCarrera")
    params = ()
    if request.args.get("nivel"):
        sql += " WHERE a.nivel = ?"
        params = (entero(request.args["nivel"], "El nivel"),)
    return jsonify(consultar(sql + " ORDER BY a.nivel, a.nombre", params))


@bp.post("/api/asignaturas")
@SOLO
def asignaturas_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["codigo", "nombre", "nivel", "carrera"]):
        return error("Código, nombre, nivel y carrera son obligatorios")
    codigo = str(d["codigo"]).strip().upper()[:20]
    nivel = entero(d["nivel"], "El nivel", 1, 10)
    horas = entero(d.get("horas_semanales") or 4, "Las horas semanales", 1, 20)
    if consultar("SELECT 1 AS x FROM Asignatura WHERE codigo = ?", (codigo,)):
        return error("Ya existe una asignatura con ese código", 409)
    id_carrera, _ = carrera(d["carrera"])
    nuevo = insertar(
        "INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales, idDocente) "
        "OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?)",
        (codigo, d["nombre"].strip(), nivel, id_carrera, horas, d.get("docente_id") or None))
    return jsonify(id=nuevo), 201


@bp.put("/api/asignaturas/<int:id_>/docente")
@SOLO
def asignaturas_docente(id_):
    d = request.get_json(silent=True) or {}
    ejecutar("UPDATE Asignatura SET idDocente = ? WHERE id = ?", (d.get("docente_id") or None, id_))
    return jsonify(ok=True)


# ------------------------------------------------------------------ salones
@bp.get("/api/salones")
@SOLO
def salones_listar():
    base = ("SELECT id, numeroDeSalon AS numero, capacidad, tipoSalon AS tipo, estado FROM Salon")
    if request.args.get("tipo"):
        return jsonify(consultar(base + " WHERE tipoSalon = ? ORDER BY numeroDeSalon", (request.args["tipo"],)))
    return jsonify(consultar(base + " ORDER BY tipoSalon, numeroDeSalon"))


@bp.post("/api/salones")
@SOLO
def salones_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["numero", "capacidad", "tipo"]):
        return error("Número, capacidad y tipo son obligatorios")
    if d["tipo"] not in TIPOS_SALON:
        return error("Tipo de salón inválido")
    numero = entero(d["numero"], "El número", 1)
    capacidad = entero(d["capacidad"], "La capacidad", 1, 500)
    nombre = "%s %d" % (d["tipo"], numero)
    if (consultar("SELECT 1 AS x FROM Salon WHERE numeroDeSalon = ?", (numero,))
            or consultar("SELECT 1 AS x FROM Salon WHERE nombre = ?", (nombre,))):
        return error("Ya existe un aula o laboratorio con ese número", 409)
    nuevo = insertar("INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) "
                     "OUTPUT INSERTED.id VALUES (?, ?, ?, ?)", (numero, nombre, capacidad, d["tipo"]))
    return jsonify(id=nuevo), 201


@bp.put("/api/salones/<int:id_>/estado")
@SOLO
def salones_estado(id_):
    d = request.get_json(silent=True) or {}
    if d.get("estado") not in ESTADOS_SALON:
        return error("Estado inválido")
    ejecutar("UPDATE Salon SET estado = ? WHERE id = ?", (d["estado"], id_))
    return jsonify(ok=True)


@bp.delete("/api/salones/<int:id_>")
@SOLO
def salones_eliminar(id_):
    if (consultar("SELECT TOP 1 1 AS x FROM Horario WHERE idSalon = ?", (id_,))
            or consultar("SELECT TOP 1 1 AS x FROM Tutoria WHERE idSalon = ?", (id_,))):
        return error("Tiene horarios o tutorías asignados; elimínalos primero", 409)
    ejecutar("DELETE FROM Salon WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ horarios
SQL_HORARIOS = (
    "SELECT h.id, " + NOMBRE_DIA + " AS dia, DATEPART(HOUR, h.horaInicio) AS hora_inicio, "
    "DATEPART(HOUR, h.horaFin) AS hora_fin, h.paralelo, p.nombre AS periodo, a.nombre AS asignatura, "
    "a.nivel, c.nombre AS carrera, s.numeroDeSalon AS salon, d.nombre AS doc_nombre, d.apellido AS doc_apellido "
    "FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo JOIN Asignatura a ON a.id = h.idAsignatura "
    "JOIN Carrera c ON c.id = a.idCarrera LEFT JOIN Salon s ON s.id = h.idSalon "
    "LEFT JOIN Docente d ON d.id = h.idDocente")


def _hhmm(hora):
    return "%02d:00" % hora


def _choca(existentes, dia, ini, fin, salon, docente, nivel, id_carrera, paralelo):
    """True si el salón, el docente o el grupo (carrera+nivel+paralelo) ya están ocupados."""
    for e in existentes:
        if e["dia"] != dia or not (e["ini"] < fin and ini < e["fin"]):
            continue
        if e["salon"] == salon or (docente and e["docente"] == docente) or \
           (e["nivel"] == nivel and e["carrera"] == id_carrera and e["paralelo"] == paralelo):
            return True
    return False


def _existentes(periodo):
    return [{"dia": r["dia"], "ini": r["ini"], "fin": r["fin"], "salon": r["idSalon"], "docente": r["idDocente"],
             "nivel": r["nivel"], "carrera": r["idCarrera"], "paralelo": r["paralelo"]}
            for r in consultar(
                "SELECT h.dia, DATEPART(HOUR, h.horaInicio) AS ini, DATEPART(HOUR, h.horaFin) AS fin, h.idSalon, "
                "h.idDocente, a.nivel, a.idCarrera, h.paralelo FROM Horario h JOIN Asignatura a ON a.id = h.idAsignatura "
                "WHERE h.idPeriodo = ?", (periodo,))]


@bp.get("/api/horarios")
@SOLO
def horarios_listar():
    cond, params = [], []
    if request.args.get("nivel"):
        cond.append("a.nivel = ?"); params.append(entero(request.args["nivel"], "El nivel"))
    if request.args.get("periodo"):
        cond.append("p.nombre = ?"); params.append(request.args["periodo"])
    sql = SQL_HORARIOS + (" WHERE " + " AND ".join(cond) if cond else "") + " ORDER BY h.horaInicio"
    return jsonify(consultar(sql, tuple(params)))


@bp.post("/api/horarios")
@SOLO
def horarios_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["asignatura_id", "salon_id", "dia", "hora_inicio", "hora_fin", "paralelo", "periodo"]):
        return error("Completa todos los campos del horario")
    ini, fin = entero(d["hora_inicio"], "La hora de inicio"), entero(d["hora_fin"], "La hora de fin")
    if not (HORA_APERTURA <= ini < fin <= HORA_CIERRE) or d["dia"] not in DIAS:
        return error("Rango inválido: use horas entre %d y %d y días de lunes a viernes" % (HORA_APERTURA, HORA_CIERRE))
    asig = consultar_uno("SELECT * FROM Asignatura WHERE id = ?", (entero(d["asignatura_id"], "La asignatura"),))
    salon = consultar_uno("SELECT * FROM Salon WHERE id = ?", (entero(d["salon_id"], "El salón"),))
    if not asig or not salon:
        return error("Asignatura o salón inexistente", 404)
    if salon["estado"] == "Mantenimiento":
        return error("El salón está en mantenimiento")
    pid, paralelo, dia = periodo_id(d["periodo"]), str(d["paralelo"]).strip().upper()[:5], DIAS.index(d["dia"]) + 1
    if _choca(_existentes(pid), dia, ini, fin, salon["id"], asig["idDocente"], asig["nivel"], asig["idCarrera"], paralelo):
        return error("Cruce de horario: el salón, el docente o el grupo ya están ocupados en ese rango", 409)
    try:
        nuevo = insertar(
            "INSERT INTO Horario (idPeriodo, idAsignatura, idDocente, idSalon, paralelo, dia, horaInicio, horaFin) "
            "OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (pid, asig["id"], asig["idDocente"], salon["id"], paralelo, dia, _hhmm(ini), _hhmm(fin)))
    except pyodbc.IntegrityError:
        return error("Esa asignatura ya tiene un bloque a esa hora en ese paralelo", 409)
    return jsonify(id=nuevo), 201


@bp.delete("/api/horarios/<int:id_>")
@SOLO
def horarios_eliminar(id_):
    ejecutar("DELETE FROM Horario WHERE id = ?", (id_,))
    return jsonify(ok=True)


@bp.post("/api/horarios/limpiar")
@SOLO
def horarios_limpiar():
    d = request.get_json(silent=True) or {}
    ejecutar("DELETE h FROM Horario h JOIN Asignatura a ON a.id = h.idAsignatura "
             "JOIN PeriodoAcademico p ON p.id = h.idPeriodo WHERE p.nombre = ? AND a.nivel = ?",
             (d.get("periodo"), entero(d.get("nivel", 0), "El nivel")))
    return jsonify(ok=True)


@bp.post("/api/horarios/generar")
@SOLO
def horarios_generar():
    """Generación automática: bloques de 2 h repartidos en días distintos, sin cruces."""
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["nivel", "periodo"]):
        return error("Indica nivel y periodo")
    nivel, paralelo = entero(d["nivel"], "El nivel"), str(d.get("paralelo") or "A").strip().upper()[:5]
    pid = periodo_id(d["periodo"])
    salones = consultar("SELECT id FROM Salon WHERE estado <> 'Mantenimiento' ORDER BY capacidad, numeroDeSalon")
    if not salones:
        return error("No hay salones disponibles")
    asignaturas = consultar("SELECT * FROM Asignatura WHERE nivel = ?", (nivel,))
    existentes, nuevos, sin_ubicar = _existentes(pid), [], []

    for a in asignaturas:
        ya = consultar_uno("SELECT COUNT(*) AS n FROM Horario WHERE idAsignatura = ? AND idPeriodo = ? AND paralelo = ?",
                           (a["id"], pid, paralelo))["n"]
        if ya:
            continue
        if not a["idDocente"]:
            sin_ubicar.append("%s (sin docente asignado)" % a["nombre"])
            continue
        dias_usados = set()
        for _ in range(math.ceil(a["horasSemanales"] / 2)):
            colocado = False
            for dia in [x for x in range(1, 6) if x not in dias_usados] or range(1, 6):
                for ini in range(HORA_APERTURA, HORA_CIERRE - 1):
                    for s in salones:
                        if not _choca(existentes, dia, ini, ini + 2, s["id"], a["idDocente"], a["nivel"],
                                      a["idCarrera"], paralelo):
                            bloque = dict(dia=dia, ini=ini, fin=ini + 2, salon=s["id"], docente=a["idDocente"],
                                          nivel=a["nivel"], carrera=a["idCarrera"], paralelo=paralelo)
                            existentes.append(bloque)
                            nuevos.append((pid, a["id"], a["idDocente"], s["id"], paralelo, dia, _hhmm(ini), _hhmm(ini + 2)))
                            dias_usados.add(dia); colocado = True
                            break
                    if colocado: break
                if colocado: break
            if not colocado:
                sin_ubicar.append("%s (sin espacio disponible)" % a["nombre"])
    if nuevos:
        with transaccion() as cur:
            for fila in nuevos:
                cur.execute("INSERT INTO Horario (idPeriodo, idAsignatura, idDocente, idSalon, paralelo, dia, "
                            "horaInicio, horaFin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", fila)
    return jsonify(creados=len(nuevos), sin_ubicar=sin_ubicar)


# ------------------------------------------------------------------ claves
@bp.get("/api/claves/solicitudes")
@SOLO
def claves_listar():
    return jsonify(consultar(
        "SELECT TOP 100 id, correo, fecha, estado FROM SolicitudClave "
        "ORDER BY CASE estado WHEN 'Pendiente' THEN 0 ELSE 1 END, id DESC"))


@bp.post("/api/claves/solicitudes/<int:id_>/atender")
@SOLO
def claves_atender(id_):
    s = consultar_uno("SELECT correo, estado FROM SolicitudClave WHERE id = ?", (id_,))
    if not s or s["estado"] != "Pendiente":
        return error("La solicitud ya fue atendida", 409)
    try:
        clave = usuarios.restablecer_clave(s["correo"])
    except ValueError as e:
        ejecutar("UPDATE SolicitudClave SET estado = 'Rechazada' WHERE id = ?", (id_,))
        return error(str(e), 404)
    ejecutar("UPDATE SolicitudClave SET estado = 'Atendida' WHERE id = ?", (id_,))
    return jsonify(correo=s["correo"], clave=clave)


@bp.post("/api/claves/restablecer")
@SOLO
def claves_restablecer():
    correo = ((request.get_json(silent=True) or {}).get("correo") or "").strip().lower()
    if not usuarios.CORREO_RE.match(correo):
        return error("Ingresa un correo válido")
    return jsonify(correo=correo, clave=usuarios.restablecer_clave(correo))


# ------------------------------------------------------------------ reportes
REPORTES = {
    "horarios": (SQL_HORARIOS + " ORDER BY h.dia, h.horaInicio",
                 ["asignatura", "nivel", "carrera", "dia", "hora_inicio", "hora_fin", "salon", "paralelo",
                  "periodo", "doc_nombre", "doc_apellido"]),
    "docentes": ("SELECT cedula, nombre, apellido, especialidad, asignatura, nivel, CAST(estado AS INT) AS estado FROM Docente",
                 ["cedula", "nombre", "apellido", "especialidad", "asignatura", "nivel", "estado"]),
    "estudiantes": ("SELECT cedula, codigoRegistro AS codigo_registro, nombre, apellido, "
                    "correoInstitucional AS correo_institucional, curso, carrera, nivel, asignatura FROM Estudiante",
                    ["cedula", "codigo_registro", "nombre", "apellido", "correo_institucional", "curso", "carrera",
                     "nivel", "asignatura"]),
    "salones": ("SELECT numeroDeSalon AS numero, tipoSalon AS tipo, capacidad, estado FROM Salon",
                ["numero", "tipo", "capacidad", "estado"]),
    "asignaturas": ("SELECT a.codigo, a.nombre, a.nivel, c.nombre AS carrera, a.horasSemanales AS horas_semanales "
                    "FROM Asignatura a JOIN Carrera c ON c.id = a.idCarrera",
                    ["codigo", "nombre", "nivel", "carrera", "horas_semanales"]),
}


@bp.get("/api/reportes/<tipo>.csv")
@SOLO
def reporte_csv(tipo):
    if tipo not in REPORTES:
        abort(404)
    sql, columnas = REPORTES[tipo]
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=columnas, extrasaction="ignore")
    escritor.writeheader()
    escritor.writerows(consultar(sql))
    return Response("\ufeff" + buffer.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=%s.csv" % tipo})


@bp.get("/api/resumen")
@SOLO
def resumen():
    cuenta = lambda t: consultar("SELECT COUNT(*) AS n FROM %s" % t)[0]["n"]  # noqa: E731
    datos = {"estudiantes": cuenta("Estudiante"), "docentes": cuenta("Docente"),
             "asignaturas": cuenta("Asignatura"), "horarios": cuenta("Horario")}
    for clave, tipo in (("aulas", "Aula"), ("laboratorios", "Laboratorio")):
        datos[clave] = consultar("SELECT COUNT(*) AS n FROM Salon WHERE tipoSalon = ?", (tipo,))[0]["n"]
    return jsonify(datos)
