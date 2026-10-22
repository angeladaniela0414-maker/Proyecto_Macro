"""Portal de Gestión Académica ULEAM: login + CRUD de las tablas de BD_Gestion_Horario."""
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException

import conexion_db as db
import os
from flask import send_from_directory
PUERTO = 5000          # cámbialo a 80 si quieres entrar sin escribir el puerto
app = Flask(__name__, template_folder="interfaz")
app.secret_key = "cambia-esta-clave-secreta"

BASE = os.path.dirname(os.path.abspath(__file__))


@app.route("/static/<path:ruta>", endpoint="static")
def archivos(ruta):
    """Sirve solo las carpetas css, js e img (nunca app.py ni conexion_db.py)."""
    if ruta.split("/")[0] not in ("css", "js", "img"):
        abort(404)
    return send_from_directory(BASE, ruta)

TABLAS = [
    "Estudiante", "Docente", "Gestion_Academica", "Administrador",
    "Facultad", "Carrera", "PeriodoAcademico", "Asignatura", "Salon",
    "Horario", "Tutoria", "TutoriaSolicitud", "Registro", "SolicitudClave",
]
# Estas tablas dependen de Usuario (id = Usuario.id): al crear se inserta primero el Usuario.
VINCULADAS = {"Docente", "Estudiante", "Gestion_Academica"}
CLAVE = "contraseña"


# ---------------------------------------------------------------- acceso
@app.before_request
def proteger():
    if request.endpoint in (None, "static", "pagina_login", "api_login"):
        return None
    if "usuario" not in session:
        if request.path.startswith("/api/"):
            return jsonify(error="La sesión expiró. Vuelve a iniciar sesión."), 401
        return redirect(url_for("pagina_login"))
    return None


@app.get("/")
def pagina_login():
    if "usuario" in session:
        return redirect(url_for("pagina_panel"))
    return render_template("login.html")


@app.get("/panel")
def pagina_panel():
    return render_template("panel.html", **session["usuario"])


@app.get("/salir")
def salir():
    session.clear()
    return redirect(url_for("pagina_login"))


@app.post("/api/login")
def api_login():
    datos = request.get_json(silent=True) or {}
    correo = (datos.get("correo") or "").strip()
    clave = datos.get("clave") or ""
    if not correo or not clave:
        return jsonify(error="Escribe tu correo institucional y tu contraseña."), 400

    admin = db.consultar(
        f"SELECT id FROM dbo.Administrador WHERE correoInstitucional = ? AND [{CLAVE}] = ?",
        (correo, clave))
    if admin:
        session["usuario"] = {"nombre": "Administrador", "rol": "Administrador"}
        return jsonify(ok=True)

    gestor = db.consultar(
        f"""SELECT g.nombre, g.apellido FROM dbo.Gestion_Academica g
            JOIN dbo.Usuario u ON u.id = g.id
            WHERE u.correoInstitucional = ? AND u.[{CLAVE}] = ?""",
        (correo, clave))
    if gestor:
        g = gestor[0]
        session["usuario"] = {"nombre": f"{g['nombre']} {g['apellido']}", "rol": "Gestión académica"}
        return jsonify(ok=True)

    return jsonify(error="Correo o contraseña incorrectos."), 401


# ------------------------------------------------------ estructura de tablas
def validar(tabla):
    if tabla not in TABLAS:
        abort(404)


def tipo_ui(c):
    t = c["tipo"]
    if c["nombre"] == CLAVE:
        return "password"
    if t in ("int", "smallint", "tinyint", "bigint"):
        return "number"
    if t == "bit":
        return "bit"
    if t == "date":
        return "date"
    if t == "time":
        return "time"
    if t.startswith("datetime") or t == "smalldatetime":
        return "datetime"
    return "text"


def estructura(tabla):
    cols = db.consultar(
        """SELECT c.name AS nombre, ty.name AS tipo, c.is_nullable AS nulo, c.is_identity AS ident,
                  c.max_length AS largo,
                  CASE WHEN dc.object_id IS NULL THEN 0 ELSE 1 END AS tiene_default
           FROM sys.columns c
           JOIN sys.types ty ON ty.user_type_id = c.user_type_id
           LEFT JOIN sys.default_constraints dc
                  ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
           WHERE c.object_id = OBJECT_ID(?)
           ORDER BY c.column_id""", (f"dbo.{tabla}",))
    fks = db.consultar(
        """SELECT cp.name AS columna, OBJECT_NAME(fkc.referenced_object_id) AS ref
           FROM sys.foreign_key_columns fkc
           JOIN sys.columns cp ON cp.object_id = fkc.parent_object_id
                              AND cp.column_id = fkc.parent_column_id
           WHERE fkc.parent_object_id = OBJECT_ID(?)""", (f"dbo.{tabla}",))
    if not cols:
        abort(404)
    return {
        "cols": cols,
        "fks": {f["columna"]: f["ref"] for f in fks},
        "vinculada": tabla in VINCULADAS,
        "tiene_correo": any(c["nombre"] == "correoInstitucional" for c in cols),
    }


def campos_formulario(tabla):
    e = estructura(tabla)
    lista = []
    for c in e["cols"]:
        if c["ident"] or c["nombre"] == "id":
            continue
        largo = c["largo"]
        if c["tipo"] in ("nvarchar", "nchar") and largo > 0:
            largo //= 2
        lista.append({
            "nombre": c["nombre"],
            "tipo": tipo_ui(c),
            "nulo": bool(c["nulo"]),
            "default": bool(c["tiene_default"]),
            "obligatorio": (not c["nulo"]) and not c["tiene_default"],
            "max": largo if c["tipo"] in ("varchar", "nvarchar", "char", "nchar") and largo > 0 else None,
            "ref": e["fks"].get(c["nombre"]),
        })
    if e["vinculada"]:
        # correo y contraseña viven en la tabla Usuario
        if not e["tiene_correo"]:
            lista.insert(0, {"nombre": "correoUsuario", "tipo": "text", "nulo": False, "default": False,
                             "obligatorio": True, "max": 120, "ref": None})
        lista.append({"nombre": CLAVE, "tipo": "password", "nulo": False, "default": False,
                      "obligatorio": True, "max": 255, "ref": None})
    return e, lista


def valor(campo, v):
    if v is None or v == "":
        return None
    t = campo["tipo"]
    if t == "number":
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError(f"El campo «{campo['nombre']}» debe ser un número entero.")
    if t == "bit":
        return 1 if str(v).lower() in ("1", "true") else 0
    if t == "datetime":
        v = str(v).replace(" ", "T")
        return v + ":00" if len(v) == 16 else v
    return v


def leer(campos, datos, crear):
    valores = {}
    for c in campos:
        v = valor(c, datos.get(c["nombre"]))
        if v is None and c["obligatorio"] and not (c["tipo"] == "password" and not crear):
            raise ValueError(f"El campo «{c['nombre']}» es obligatorio.")
        valores[c["nombre"]] = v
    return valores


def propios(campos, vinculada):
    """Campos que pertenecen realmente a la tabla (sin los de Usuario)."""
    if not vinculada:
        return campos
    return [c for c in campos if c["nombre"] not in ("correoUsuario", CLAVE)]


# -------------------------------------------------------------------- CRUD
@app.get("/api/<tabla>")
def listar(tabla):
    validar(tabla)
    e, campos = campos_formulario(tabla)
    sel, nombres = [], []
    for c in e["cols"]:
        n, t = c["nombre"], c["tipo"]
        if n == CLAVE:
            continue
        ref = f"t.[{n}]"
        if t == "date":
            sel.append(f"CONVERT(varchar(10), {ref}, 23) AS [{n}]")
        elif t == "time":
            sel.append(f"CONVERT(varchar(5), {ref}, 108) AS [{n}]")
        elif t.startswith("datetime") or t == "smalldatetime":
            sel.append(f"CONVERT(varchar(16), {ref}, 120) AS [{n}]")
        else:
            sel.append(f"{ref} AS [{n}]")
        nombres.append(n)

    union = ""
    if e["vinculada"]:
        union = "LEFT JOIN dbo.Usuario u ON u.id = t.id"
        if not e["tiene_correo"]:
            sel.append("u.correoInstitucional AS [correoUsuario]")
            nombres.append("correoUsuario")

    filas = db.consultar(f"SELECT {', '.join(sel)} FROM dbo.[{tabla}] t {union} ORDER BY t.id")
    refs = {k: v for k, v in e["fks"].items() if k != "id"}
    return jsonify(campos=campos, columnas=nombres, refs=refs, filas=filas)


@app.get("/api/<tabla>/opciones")
def opciones(tabla):
    """Lista id + texto para llenar los desplegables de claves foráneas."""
    validar(tabla)
    nombres = {c["nombre"] for c in estructura(tabla)["cols"]}
    partes = [n for n in ("codigo", "nombre", "apellido") if n in nombres]
    if not partes and "correoInstitucional" in nombres:
        partes = ["correoInstitucional"]
    sel = "id" + "".join(f", [{p}]" for p in partes)
    resultado = []
    for f in db.consultar(f"SELECT {sel} FROM dbo.[{tabla}] ORDER BY id"):
        texto = " ".join(str(f[p]) for p in partes if p != "codigo" and f[p] is not None)
        if "codigo" in partes and f["codigo"] is not None:
            texto = f"{f['codigo']} - {texto}" if texto else str(f["codigo"])
        resultado.append({"id": f["id"], "texto": texto or f"#{f['id']}"})
    return jsonify(resultado)


@app.post("/api/<tabla>")
def crear(tabla):
    validar(tabla)
    e, campos = campos_formulario(tabla)
    v = leer(campos, request.get_json(silent=True) or {}, True)
    reales = propios(campos, e["vinculada"])

    with db.transaccion() as cur:
        nuevo_id = None
        if e["vinculada"]:
            correo = v.get("correoInstitucional") or v.get("correoUsuario")
            cur.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM dbo.Usuario WITH (UPDLOCK, HOLDLOCK)")
            nuevo_id = cur.fetchone()[0]
            cur.execute(f"INSERT INTO dbo.Usuario (id, correoInstitucional, [{CLAVE}]) VALUES (?, ?, ?)",
                        nuevo_id, correo, v[CLAVE])
        elif not any(c["ident"] for c in e["cols"]):
            cur.execute(f"SELECT ISNULL(MAX(id), 0) + 1 FROM dbo.[{tabla}] WITH (UPDLOCK, HOLDLOCK)")
            nuevo_id = cur.fetchone()[0]

        cols, vals = [], []
        if nuevo_id is not None:
            cols.append("[id]")
            vals.append(nuevo_id)
        for c in reales:
            x = v.get(c["nombre"])
            if x is None and c["default"]:
                continue          # deja que SQL Server use el valor predeterminado
            cols.append(f"[{c['nombre']}]")
            vals.append(x)
        cur.execute(f"INSERT INTO dbo.[{tabla}] ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", vals)
    return jsonify(ok=True)


@app.put("/api/<tabla>/<int:id>")
def editar(tabla, id):
    validar(tabla)
    e, campos = campos_formulario(tabla)
    v = leer(campos, request.get_json(silent=True) or {}, False)
    reales = propios(campos, e["vinculada"])

    with db.transaccion() as cur:
        sets, params = [], []
        for c in reales:
            x = v.get(c["nombre"])
            if x is None and (c["tipo"] == "password" or not c["nulo"]):
                continue          # contraseña en blanco o dato sin valor: se conserva el actual
            sets.append(f"[{c['nombre']}] = ?")
            params.append(x)
        if sets:
            cur.execute(f"UPDATE dbo.[{tabla}] SET {', '.join(sets)} WHERE id = ?", params + [id])

        if e["vinculada"]:
            correo = v.get("correoInstitucional") or v.get("correoUsuario")
            if v.get(CLAVE):
                cur.execute(f"UPDATE dbo.Usuario SET correoInstitucional = ?, [{CLAVE}] = ? WHERE id = ?",
                            correo, v[CLAVE], id)
            else:
                cur.execute("UPDATE dbo.Usuario SET correoInstitucional = ? WHERE id = ?", correo, id)
    return jsonify(ok=True)


@app.delete("/api/<tabla>/<int:id>")
def eliminar(tabla, id):
    validar(tabla)
    with db.transaccion() as cur:
        cur.execute(f"DELETE FROM dbo.[{tabla}] WHERE id = ?", id)
        if tabla in VINCULADAS:
            cur.execute("DELETE FROM dbo.Usuario WHERE id = ?", id)
    return jsonify(ok=True)


# ----------------------------------------------------------------- errores
@app.errorhandler(Exception)
def manejar_error(e):
    if isinstance(e, HTTPException):
        return e
    texto = str(e)
    if isinstance(e, ValueError):
        mensaje = texto
    elif "(547)" in texto:
        mensaje = ("La base de datos no lo permite: el registro está relacionado con otros datos "
                   "o incumple una regla (por ejemplo, la hora de fin debe ser mayor que la de inicio).")
    elif "(2627)" in texto or "(2601)" in texto:
        mensaje = "Ya existe un registro con ese mismo valor único (cédula, correo, código, nombre...)."
    else:
        app.logger.exception(e)
        mensaje = "Error en la base de datos: " + texto[:300]
    return jsonify(error=mensaje), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PUERTO, debug=True)
