"""
Servidor Flask - Sistema de Gestión Académica.
Ejecutar:  python app.py   ->   http://127.0.0.1:5000   (usuario: admin / clave: Admin2026)
"""
import csv
import io
import math
import os
import unicodedata
from functools import wraps

from flask import (Flask, Response, abort, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

import conexion_db as db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
HORA_APERTURA, HORA_CIERRE = 7, 21
SECCIONES = {"inicio", "estudiantes", "docentes", "aulas", "laboratorios",
             "generacion_horarios", "asignaturas", "exportar_reportes"}
ESTADOS_SALON = {"Disponible", "Ocupado", "Mantenimiento"}
TIPOS_SALON = {"Aula", "Laboratorio", "Auditorio"}
LONGITUD_CEDULA = 10
DOMINIO_CORREO = "universidad.edu.ec"


# ------------------------------------------------------------------ utilidades
def login_requerido(f):
    @wraps(f)
    def envoltura(*a, **kw):
        if "usuario" not in session:
            if request.path.startswith("/api/") or request.path.startswith("/seccion/"):
                return jsonify(error="Sesión expirada"), 401
            return redirect(url_for("login"))
        return f(*a, **kw)
    return envoltura


def error(msg, codigo=400):
    return jsonify(error=msg), codigo


def faltantes(datos, campos):
    return [c for c in campos if datos.get(c) in (None, "")]


def entero(valor, nombre, minimo=None, maximo=None):
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{nombre} debe ser un número entero")
    if (minimo is not None and n < minimo) or (maximo is not None and n > maximo):
        raise ValueError(f"{nombre} debe estar entre {minimo} y {maximo}")
    return n


def cedula_valida(valor):
    c = str(valor or "").strip()
    if not (c.isdigit() and len(c) == LONGITUD_CEDULA):
        raise ValueError(f"La cédula debe tener {LONGITUD_CEDULA} dígitos numéricos")
    return c


def solo_letras_numeros(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(ch for ch in sin_tildes.lower() if ch.isalnum())


def generar_correo(nombre, apellido, codigo):
    base = f"{solo_letras_numeros(nombre.split()[0])}.{solo_letras_numeros(apellido.split()[0])}"
    correo = f"{base}@{DOMINIO_CORREO}"
    if db.consultar("SELECT 1 AS x FROM estudiantes WHERE correo_institucional = ?", (correo,)):
        correo = f"{base}{codigo}@{DOMINIO_CORREO}"
    return correo


@app.errorhandler(ValueError)
def valor_invalido(e):
    return error(str(e))


def hay_cruce(dia, ini, fin, salon_id, docente_id, periodo, excluir_id=0):
    """True si el salón o el docente ya están ocupados en ese rango."""
    sql = ("SELECT COUNT(*) AS n FROM horarios WHERE dia = ? AND periodo = ? AND id <> ? "
           "AND hora_inicio < ? AND ? < hora_fin AND (salon_id = ?" +
           (" OR docente_id = ?)" if docente_id else ")"))
    params = [dia, periodo, excluir_id, fin, ini, salon_id] + ([docente_id] if docente_id else [])
    return db.consultar(sql, tuple(params))[0]["n"] > 0


# ------------------------------------------------------------------ páginas
@app.route("/")
def raiz():
    return redirect(url_for("index" if "usuario" in session else "login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/index")
@login_requerido
def index():
    return render_template("index.html", usuario=session["usuario"], rol=session["rol"])


@app.route("/seccion/<nombre>")
@login_requerido
def seccion(nombre):
    if nombre not in SECCIONES:
        abort(404)
    return render_template(f"secciones/{nombre}.html", dias=DIAS)


# ------------------------------------------------------------------ autenticación
@app.post("/api/login")
def api_login():
    datos = request.get_json(silent=True) or {}
    filas = db.consultar("SELECT * FROM usuarios WHERE usuario = ?", (datos.get("usuario", ""),))
    if not filas or not check_password_hash(filas[0]["clave_hash"], datos.get("clave", "")):
        return error("Usuario o contraseña incorrectos", 401)
    session["usuario"], session["rol"] = filas[0]["usuario"], filas[0]["rol"]
    return jsonify(ok=True)


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


# ------------------------------------------------------------------ docentes
@app.get("/api/docentes")
@login_requerido
def docentes_listar():
    return jsonify(db.consultar("SELECT * FROM docentes ORDER BY apellido, nombre"))


@app.post("/api/docentes")
@login_requerido
def docentes_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["cedula", "nombre", "apellido", "asignatura", "nivel"]):
        return error("Cédula, nombre, apellido, asignatura y nivel son obligatorios")
    cedula = cedula_valida(d["cedula"])
    nivel = entero(d["nivel"], "El nivel", 1, 10)
    if db.consultar("SELECT 1 AS x FROM docentes WHERE cedula = ?", (cedula,)):
        return error("Ya existe un docente con esa cédula", 409)
    nuevo = db.insertar(
        "INSERT INTO docentes (cedula, nombre, apellido, especialidad, asignatura, nivel) VALUES (?, ?, ?, ?, ?, ?)",
        (cedula, d["nombre"].strip(), d["apellido"].strip(), (d.get("especialidad") or "").strip(),
         d["asignatura"].strip(), nivel))
    return jsonify(id=nuevo), 201


@app.put("/api/docentes/<int:id_>/estado")
@login_requerido
def docentes_estado(id_):
    db.ejecutar("UPDATE docentes SET estado = 1 - estado WHERE id = ?", (id_,))
    return jsonify(ok=True)


@app.delete("/api/docentes/<int:id_>")
@login_requerido
def docentes_eliminar(id_):
    if (db.consultar("SELECT 1 AS x FROM asignaturas WHERE docente_id = ?", (id_,))
            or db.consultar("SELECT 1 AS x FROM horarios WHERE docente_id = ?", (id_,))):
        return error("El docente tiene asignaturas u horarios asignados; desactívalo en su lugar", 409)
    db.ejecutar("DELETE FROM docentes WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ estudiantes
@app.get("/api/estudiantes")
@login_requerido
def estudiantes_listar():
    return jsonify(db.consultar("SELECT * FROM estudiantes ORDER BY apellido, nombre"))


@app.post("/api/estudiantes")
@login_requerido
def estudiantes_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["cedula", "codigo_registro", "nombre", "apellido", "curso", "carrera", "nivel"]):
        return error("Cédula, código de registro, nombre, apellido, curso, carrera y nivel son obligatorios")
    cedula = cedula_valida(d["cedula"])
    codigo = entero(d["codigo_registro"], "El código de registro", 1)
    nivel = entero(d["nivel"], "El nivel", 1, 10)
    if db.consultar("SELECT 1 AS x FROM estudiantes WHERE cedula = ?", (cedula,)):
        return error("Ya existe un estudiante con esa cédula", 409)
    if db.consultar("SELECT 1 AS x FROM estudiantes WHERE codigo_registro = ?", (codigo,)):
        return error("Ya existe un estudiante con ese código de registro", 409)
    nombre, apellido = d["nombre"].strip(), d["apellido"].strip()
    correo = generar_correo(nombre, apellido, codigo)
    nuevo = db.insertar(
        "INSERT INTO estudiantes (cedula, codigo_registro, nombre, apellido, correo_institucional, curso, carrera, "
        "nivel, asignatura) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (cedula, codigo, nombre, apellido, correo, d["curso"].strip().upper(), d["carrera"].strip(),
         nivel, (d.get("asignatura") or "").strip()))
    return jsonify(id=nuevo, correo_institucional=correo), 201


@app.delete("/api/estudiantes/<int:id_>")
@login_requerido
def estudiantes_eliminar(id_):
    db.ejecutar("DELETE FROM estudiantes WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ asignaturas
@app.get("/api/asignaturas")
@login_requerido
def asignaturas_listar():
    sql = ("SELECT a.*, d.nombre AS doc_nombre, d.apellido AS doc_apellido FROM asignaturas a "
           "LEFT JOIN docentes d ON d.id = a.docente_id")
    params = ()
    if request.args.get("nivel"):
        sql += " WHERE a.nivel = ?"
        params = (int(request.args["nivel"]),)
    return jsonify(db.consultar(sql + " ORDER BY a.nivel, a.nombre", params))


@app.post("/api/asignaturas")
@login_requerido
def asignaturas_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["codigo", "nombre", "nivel", "carrera"]):
        return error("Código, nombre, nivel y carrera son obligatorios")
    if db.consultar("SELECT 1 AS x FROM asignaturas WHERE codigo = ?", (d["codigo"],)):
        return error("Ya existe una asignatura con ese código")
    nuevo = db.insertar(
        "INSERT INTO asignaturas (codigo, nombre, nivel, carrera, horas_semanales, docente_id) VALUES (?, ?, ?, ?, ?, ?)",
        (int(d["codigo"]), d["nombre"], int(d["nivel"]), d["carrera"],
         int(d.get("horas_semanales") or 4), d.get("docente_id") or None))
    return jsonify(id=nuevo), 201


@app.put("/api/asignaturas/<int:id_>/docente")
@login_requerido
def asignaturas_docente(id_):
    d = request.get_json(silent=True) or {}
    db.ejecutar("UPDATE asignaturas SET docente_id = ? WHERE id = ?", (d.get("docente_id") or None, id_))
    return jsonify(ok=True)


# ------------------------------------------------------------------ salones
@app.get("/api/salones")
@login_requerido
def salones_listar():
    tipo = request.args.get("tipo")
    if tipo:
        return jsonify(db.consultar("SELECT * FROM salones WHERE tipo = ? ORDER BY numero", (tipo,)))
    return jsonify(db.consultar("SELECT * FROM salones ORDER BY tipo, numero"))


@app.post("/api/salones")
@login_requerido
def salones_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["numero", "capacidad", "tipo"]):
        return error("Número, capacidad y tipo son obligatorios")
    if d["tipo"] not in TIPOS_SALON:
        return error("Tipo de salón inválido")
    numero = entero(d["numero"], "El número", 1)
    capacidad = entero(d["capacidad"], "La capacidad", 1, 500)
    if db.consultar("SELECT 1 AS x FROM salones WHERE numero = ?", (numero,)):
        return error("Ya existe un aula o laboratorio con ese número", 409)
    nuevo = db.insertar("INSERT INTO salones (numero, capacidad, tipo) VALUES (?, ?, ?)",
                        (numero, capacidad, d["tipo"]))
    return jsonify(id=nuevo), 201


@app.put("/api/salones/<int:id_>/estado")
@login_requerido
def salones_estado(id_):
    d = request.get_json(silent=True) or {}
    if d.get("estado") not in ESTADOS_SALON:
        return error("Estado inválido")
    db.ejecutar("UPDATE salones SET estado = ? WHERE id = ?", (d["estado"], id_))
    return jsonify(ok=True)


@app.delete("/api/salones/<int:id_>")
@login_requerido
def salones_eliminar(id_):
    if db.consultar("SELECT 1 AS x FROM horarios WHERE salon_id = ?", (id_,)):
        return error("Tiene horarios asignados; elimínalos primero", 409)
    db.ejecutar("DELETE FROM salones WHERE id = ?", (id_,))
    return jsonify(ok=True)


# ------------------------------------------------------------------ horarios
SQL_HORARIOS = ("SELECT h.id, h.dia, h.hora_inicio, h.hora_fin, h.paralelo, h.periodo, "
                "a.nombre AS asignatura, a.nivel, a.carrera, s.numero AS salon, "
                "d.nombre AS doc_nombre, d.apellido AS doc_apellido "
                "FROM horarios h JOIN asignaturas a ON a.id = h.asignatura_id "
                "JOIN salones s ON s.id = h.salon_id LEFT JOIN docentes d ON d.id = h.docente_id")


@app.get("/api/horarios")
@login_requerido
def horarios_listar():
    cond, params = [], []
    if request.args.get("nivel"):
        cond.append("a.nivel = ?"); params.append(int(request.args["nivel"]))
    if request.args.get("periodo"):
        cond.append("h.periodo = ?"); params.append(request.args["periodo"])
    sql = SQL_HORARIOS + (" WHERE " + " AND ".join(cond) if cond else "") + " ORDER BY h.hora_inicio"
    return jsonify(db.consultar(sql, tuple(params)))


@app.post("/api/horarios")
@login_requerido
def horarios_crear():
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["asignatura_id", "salon_id", "dia", "hora_inicio", "hora_fin", "paralelo", "periodo"]):
        return error("Completa todos los campos del horario")
    ini, fin = int(d["hora_inicio"]), int(d["hora_fin"])
    if not (HORA_APERTURA <= ini < fin <= HORA_CIERRE) or d["dia"] not in DIAS:
        return error(f"Rango inválido: use horas entre {HORA_APERTURA} y {HORA_CIERRE} y días de lunes a viernes")
    asig = db.consultar("SELECT * FROM asignaturas WHERE id = ?", (int(d["asignatura_id"]),))
    salon = db.consultar("SELECT * FROM salones WHERE id = ?", (int(d["salon_id"]),))
    if not asig or not salon:
        return error("Asignatura o salón inexistente", 404)
    if salon[0]["estado"] == "Mantenimiento":
        return error("El salón está en mantenimiento")
    if hay_cruce(d["dia"], ini, fin, salon[0]["id"], asig[0]["docente_id"], d["periodo"]):
        return error("Cruce de horario: el salón o el docente ya están ocupados en ese rango", 409)
    nuevo = db.insertar(
        "INSERT INTO horarios (asignatura_id, docente_id, salon_id, dia, hora_inicio, hora_fin, paralelo, periodo) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (asig[0]["id"], asig[0]["docente_id"], salon[0]["id"], d["dia"], ini, fin, d["paralelo"], d["periodo"]))
    return jsonify(id=nuevo), 201


@app.delete("/api/horarios/<int:id_>")
@login_requerido
def horarios_eliminar(id_):
    db.ejecutar("DELETE FROM horarios WHERE id = ?", (id_,))
    return jsonify(ok=True)


@app.post("/api/horarios/limpiar")
@login_requerido
def horarios_limpiar():
    d = request.get_json(silent=True) or {}
    db.ejecutar("DELETE FROM horarios WHERE periodo = ? AND asignatura_id IN "
                "(SELECT id FROM asignaturas WHERE nivel = ?)", (d.get("periodo"), int(d.get("nivel", 0))))
    return jsonify(ok=True)


@app.post("/api/horarios/generar")
@login_requerido
def horarios_generar():
    """Generación automática: bloques de 2 h repartidos en días distintos, sin cruces."""
    d = request.get_json(silent=True) or {}
    if faltantes(d, ["nivel", "periodo"]):
        return error("Indica nivel y periodo")
    nivel, periodo, paralelo = int(d["nivel"]), d["periodo"], d.get("paralelo") or "A"
    salones = db.consultar("SELECT * FROM salones WHERE estado <> 'Mantenimiento' ORDER BY capacidad, numero")
    if not salones:
        return error("No hay salones disponibles")
    asignaturas = db.consultar("SELECT * FROM asignaturas WHERE nivel = ?", (nivel,))
    creados, sin_ubicar = 0, []

    for a in asignaturas:
        ya = db.consultar("SELECT COUNT(*) AS n FROM horarios WHERE asignatura_id = ? AND periodo = ?",
                          (a["id"], periodo))[0]["n"]
        if ya:
            continue
        if not a["docente_id"]:
            sin_ubicar.append(f"{a['nombre']} (sin docente asignado)")
            continue
        bloques, dias_usados = math.ceil(a["horas_semanales"] / 2), set()
        for _ in range(bloques):
            colocado = False
            for dia in [x for x in DIAS if x not in dias_usados] or DIAS:
                for ini in range(HORA_APERTURA, HORA_CIERRE - 1):
                    for s in salones:
                        if not hay_cruce(dia, ini, ini + 2, s["id"], a["docente_id"], periodo):
                            db.insertar(
                                "INSERT INTO horarios (asignatura_id, docente_id, salon_id, dia, hora_inicio, "
                                "hora_fin, paralelo, periodo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (a["id"], a["docente_id"], s["id"], dia, ini, ini + 2, paralelo, periodo))
                            creados += 1; dias_usados.add(dia); colocado = True
                            break
                    if colocado: break
                if colocado: break
            if not colocado:
                sin_ubicar.append(f"{a['nombre']} (sin espacio disponible)")
    return jsonify(creados=creados, sin_ubicar=sin_ubicar)


# ------------------------------------------------------------------ reportes
REPORTES = {
    "horarios": (SQL_HORARIOS + " ORDER BY h.dia, h.hora_inicio",
                 ["asignatura", "nivel", "carrera", "dia", "hora_inicio", "hora_fin", "salon", "paralelo",
                  "periodo", "doc_nombre", "doc_apellido"]),
    "docentes": ("SELECT cedula, nombre, apellido, especialidad, asignatura, nivel, estado FROM docentes",
                 ["cedula", "nombre", "apellido", "especialidad", "asignatura", "nivel", "estado"]),
    "estudiantes": ("SELECT cedula, codigo_registro, nombre, apellido, correo_institucional, curso, carrera, nivel, "
                    "asignatura FROM estudiantes",
                    ["cedula", "codigo_registro", "nombre", "apellido", "correo_institucional", "curso",
                     "carrera", "nivel", "asignatura"]),
    "salones": ("SELECT numero, tipo, capacidad, estado FROM salones", ["numero", "tipo", "capacidad", "estado"]),
    "asignaturas": ("SELECT codigo, nombre, nivel, carrera, horas_semanales FROM asignaturas",
                    ["codigo", "nombre", "nivel", "carrera", "horas_semanales"]),
}


@app.get("/api/reportes/<tipo>.csv")
@login_requerido
def reporte_csv(tipo):
    if tipo not in REPORTES:
        abort(404)
    sql, columnas = REPORTES[tipo]
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=columnas, extrasaction="ignore")
    escritor.writeheader()
    escritor.writerows(db.consultar(sql))
    return Response("\ufeff" + buffer.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={tipo}.csv"})


@app.get("/api/resumen")
@login_requerido
def resumen():
    cuenta = lambda t: db.consultar(f"SELECT COUNT(*) AS n FROM {t}")[0]["n"]  # noqa: E731
    datos = {t: cuenta(t) for t in ("estudiantes", "docentes", "asignaturas", "horarios")}
    for clave, tipo in (("aulas", "Aula"), ("laboratorios", "Laboratorio")):
        datos[clave] = db.consultar("SELECT COUNT(*) AS n FROM salones WHERE tipo = ?", (tipo,))[0]["n"]
    return jsonify(datos)


if __name__ == "__main__":
    db.inicializar()
    print(f"[DB] Motor en uso: {db.MOTOR}")
    app.run(debug=True)
