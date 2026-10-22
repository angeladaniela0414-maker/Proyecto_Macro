"""Todo el SQL del sistema. Lee los datos que carga el programa de ingreso de datos.

Tablas que usa (BD_Gestion_Horario):
  Usuario, Gestion_Academica, Docente, Estudiante, Administrador       (02_Usuarios.sql)
  Carrera, PeriodoAcademico, Asignatura, Salon, Horario                (las crea/llena el programa de datos)
Este sistema solo ESCRIBE en Horario (generar / descartar horarios). Nada más.
Si tus tablas usan otros nombres de columna, se ajustan aquí.
"""
import math
from datetime import datetime

import pyodbc

import db

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes"}
HORA_APERTURA, HORA_CIERRE = 7, 21           # los bloques generados van de 7:00 a 21:00
TABLAS = ["Usuario", "Docente", "Estudiante", "Gestion_Academica", "Carrera", "PeriodoAcademico",
          "Asignatura", "Salon", "Horario"]


def entero(v, defecto=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return defecto


def verificar_tablas():
    """Devuelve la lista de tablas que faltan en la base."""
    existentes = {f["name"].lower() for f in db.consultar("SELECT name FROM sys.tables")}
    return [t for t in TABLAS if t.lower() not in existentes]


# ==============================================================================
# Ingreso
# ==============================================================================
def datos_de_acceso(usuario):
    """Busca la cuenta por correo (o por la parte anterior a la @). Devuelve dict o None."""
    candidatos = [usuario] + ([usuario + "@live.uleam.edu.ec"] if "@" not in usuario else [])
    for correo in candidatos:
        f = db.uno("SELECT id, correoInstitucional AS correo, [contraseña] AS clave FROM Usuario "
                   "WHERE correoInstitucional = ?", (correo,))
        if f:
            return _con_rol(f)
    a = db.uno("SELECT id, correoInstitucional AS correo, [contraseña] AS clave FROM Administrador "
               "WHERE correoInstitucional = ?", (usuario,))
    if a:
        return dict(a, rol="gestion", nombre="Administrador", apellido="", activo=True)
    return None


def _con_rol(f):
    for rol, sql in (("estudiante", "SELECT nombre, apellido, 1 AS activo FROM Estudiante WHERE id = ?"),
                     ("docente", "SELECT nombre, apellido, CAST(estado AS INT) AS activo FROM Docente WHERE id = ?"),
                     ("gestion", "SELECT nombre, apellido, 1 AS activo FROM Gestion_Academica WHERE id = ?")):
        p = db.uno(sql, (f["id"],))
        if p:
            return dict(f, rol=rol, nombre=p["nombre"], apellido=p["apellido"], activo=bool(p["activo"]))
    return dict(f, rol=None, nombre="", apellido="", activo=False)


# ==============================================================================
# Catálogos (para los filtros)
# ==============================================================================
def periodo_activo():
    return db.uno("SELECT TOP 1 id, nombre FROM PeriodoAcademico WHERE activo = 1 ORDER BY id DESC")


def catalogos():
    return {
        "periodos": db.consultar("SELECT id, nombre, activo FROM PeriodoAcademico ORDER BY id DESC"),
        "carreras": db.consultar("SELECT id, nombre FROM Carrera ORDER BY nombre"),
        "niveles": db.consultar("SELECT DISTINCT nivel FROM Asignatura ORDER BY nivel"),
        "paralelos": db.consultar(
            "SELECT DISTINCT p FROM (SELECT UPPER(RIGHT(RTRIM(curso), 1)) AS p FROM Estudiante WHERE curso IS NOT NULL "
            "UNION SELECT paralelo FROM Horario) x WHERE p <> '' ORDER BY p"),
        "asignaturas": db.consultar("SELECT id, nombre, nivel FROM Asignatura ORDER BY nivel, nombre"),
        "docentes": db.consultar("SELECT id, nombre + ' ' + apellido AS nombre FROM Docente WHERE estado = 1 "
                                 "ORDER BY apellido, nombre"),
        "salones": db.consultar("SELECT id, nombre FROM Salon ORDER BY nombre"),
    }


def perfil_estudiante(uid):
    return db.uno(
        "SELECT e.id, e.nombre, e.apellido, e.carrera, e.nivel, e.curso, c.id AS idCarrera "
        "FROM Estudiante e LEFT JOIN Carrera c ON c.nombre = e.carrera WHERE e.id = ?", (uid,))


def letra_paralelo(curso):
    partes = (curso or "").strip().split()
    return partes[-1].upper()[:5] if partes else ""


# ==============================================================================
# Horarios
# ==============================================================================
_SQL_HORARIO = """
SELECT h.id, h.dia,
       CONVERT(VARCHAR(5), h.horaInicio, 108) AS horaInicio, CONVERT(VARCHAR(5), h.horaFin, 108) AS horaFin,
       h.paralelo, a.nombre AS asignatura, a.codigo, a.nivel, c.id AS idCarrera, c.nombre AS carrera,
       d.nombre + ' ' + d.apellido AS docente, s.nombre AS salon, p.nombre AS periodo
FROM Horario h
JOIN PeriodoAcademico p ON p.id = h.idPeriodo
JOIN Asignatura a ON a.id = h.idAsignatura
JOIN Carrera c ON c.id = a.idCarrera
LEFT JOIN Docente d ON d.id = h.idDocente
LEFT JOIN Salon s ON s.id = h.idSalon
"""


def horario(periodo=None, carrera=None, nivel=None, paralelo=None, asignatura=None, docente=None, salon=None):
    cond, par = [], []
    if periodo:
        cond.append("h.idPeriodo = ?"); par.append(periodo)
    else:
        cond.append("p.activo = 1")
    for sql, valor in (("c.id = ?", carrera), ("a.nivel = ?", nivel), ("h.paralelo = ?", paralelo),
                       ("a.id = ?", asignatura), ("h.idDocente = ?", docente), ("h.idSalon = ?", salon)):
        if valor:
            cond.append(sql); par.append(valor)
    return db.consultar(_SQL_HORARIO + " WHERE " + " AND ".join(cond) +
                        " ORDER BY h.horaInicio, h.dia, a.nivel, h.paralelo", par)


def _min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def horas_semanales(bloques):
    return sum((_min(b["horaFin"]) - _min(b["horaInicio"])) / 60.0 for b in bloques)


def resumen_asignaturas(bloques):
    res = {}
    for b in bloques:
        r = res.setdefault((b["asignatura"], b["paralelo"], b["nivel"]), dict(
            asignatura=b["asignatura"], paralelo=b["paralelo"], nivel=b["nivel"], docente=b["docente"],
            horas=0.0, salones=set()))
        r["horas"] += (_min(b["horaFin"]) - _min(b["horaInicio"])) / 60.0
        if b["salon"]:
            r["salones"].add(b["salon"])
    salida = sorted(res.values(), key=lambda r: (r["nivel"], r["asignatura"]))
    for r in salida:
        r["salones"] = ", ".join(sorted(r["salones"]))
    return salida


def matriz(bloques):
    """Agrupa los bloques en franjas (filas) × días (columnas). Devuelve (franjas, celdas)."""
    franjas = sorted({(b["horaInicio"], b["horaFin"]) for b in bloques})
    celdas = {}
    for b in bloques:
        celdas.setdefault(((b["horaInicio"], b["horaFin"]), b["dia"]), []).append(b)
    return franjas, celdas


# ==============================================================================
# Salones, docentes, estudiantes (solo consulta)
# ==============================================================================
def salones(tipo=None):
    ahora = datetime.now()
    hora = ahora.strftime("%H:%M")
    par = [ahora.isoweekday(), hora, hora]
    sql = ("SELECT s.id, s.numeroDeSalon AS numero, s.nombre, s.capacidad, s.tipoSalon AS tipo, s.estado, "
           "CASE WHEN EXISTS (SELECT 1 FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
           "WHERE h.idSalon = s.id AND h.dia = ? AND h.horaInicio <= CAST(? AS TIME) AND h.horaFin > CAST(? AS TIME)) "
           "THEN 1 ELSE 0 END AS ocupado FROM Salon s")
    if tipo:
        sql += " WHERE s.tipoSalon = ?"; par.append(tipo)
    return db.consultar(sql + " ORDER BY s.tipoSalon, s.nombre", par)


def salones_libres(dia, hi, hf):
    if dia not in DIAS:
        raise ValueError("Selecciona un día de lunes a viernes.")
    try:
        hi = datetime.strptime(hi, "%H:%M").strftime("%H:%M")
        hf = datetime.strptime(hf, "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        raise ValueError("Las horas no son válidas.")
    if _min(hf) <= _min(hi):
        raise ValueError("La hora final debe ser posterior a la inicial.")
    return db.consultar(
        "SELECT s.id, s.nombre, s.capacidad, s.tipoSalon AS tipo FROM Salon s WHERE s.estado = 'Disponible' "
        "AND NOT EXISTS (SELECT 1 FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
        "WHERE h.idSalon = s.id AND h.dia = ? AND h.horaInicio < CAST(? AS TIME) AND h.horaFin > CAST(? AS TIME)) "
        "ORDER BY s.tipoSalon, s.nombre", (dia, hf, hi))


def docentes():
    return db.consultar(
        "SELECT d.id, d.cedula, d.nombre, d.apellido, d.especialidad, CAST(d.estado AS INT) AS estado, "
        "u.correoInstitucional AS correo, "
        "(SELECT COUNT(DISTINCT h.idAsignatura) FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
        "WHERE h.idDocente = d.id) AS asignaturas "
        "FROM Docente d JOIN Usuario u ON u.id = d.id ORDER BY d.apellido, d.nombre")


def estudiantes(carrera=None, nivel=None, paralelo=None):
    cond, par = [], []
    if carrera:
        cond.append("c.id = ?"); par.append(carrera)
    if nivel:
        cond.append("e.nivel = ?"); par.append(nivel)
    if paralelo:
        cond.append("UPPER(RIGHT(RTRIM(e.curso), 1)) = ?"); par.append(paralelo)
    sql = ("SELECT TOP 500 e.id, e.nombre, e.apellido, e.correoInstitucional AS correo, e.carrera, e.nivel, "
           "UPPER(RIGHT(RTRIM(e.curso), 1)) AS paralelo, c.id AS idCarrera FROM Estudiante e "
           "LEFT JOIN Carrera c ON c.nombre = e.carrera")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    return db.consultar(sql + " ORDER BY e.carrera, e.nivel, e.apellido, e.nombre", par)


# ==============================================================================
# Gestión: resumen y conflictos
# ==============================================================================
def resumen_gestion(id_periodo):
    return db.uno(
        "SELECT (SELECT COUNT(*) FROM Docente WHERE estado = 1) AS docentes, "
        "(SELECT COUNT(*) FROM Estudiante) AS estudiantes, "
        "(SELECT COUNT(*) FROM Salon WHERE estado = 'Disponible') AS salones, "
        "(SELECT COUNT(*) FROM Horario WHERE idPeriodo = ?) AS bloques", (id_periodo,))


def conflictos(id_periodo):
    """Bloques que se solapan en el mismo docente o el mismo salón (por ejemplo, datos mal cargados)."""
    base = ("SELECT TOP 30 N'{tipo}' AS tipo, h1.dia, CONVERT(VARCHAR(5), h1.horaInicio, 108) AS inicio, "
            "CONVERT(VARCHAR(5), h1.horaFin, 108) AS fin, a1.nombre AS asignatura1, h1.paralelo AS paralelo1, "
            "a2.nombre AS asignatura2, h2.paralelo AS paralelo2, {quien} AS quien "
            "FROM Horario h1 JOIN Horario h2 ON h1.id < h2.id AND h1.idPeriodo = h2.idPeriodo AND h1.dia = h2.dia "
            "AND h1.horaInicio < h2.horaFin AND h2.horaInicio < h1.horaFin AND {cond} "
            "JOIN Asignatura a1 ON a1.id = h1.idAsignatura JOIN Asignatura a2 ON a2.id = h2.idAsignatura {joins} "
            "WHERE h1.idPeriodo = ?")
    docente = base.format(tipo="Docente", cond="h1.idDocente = h2.idDocente",
                          joins="JOIN Docente d ON d.id = h1.idDocente", quien="d.nombre + ' ' + d.apellido")
    salon = base.format(tipo="Salón", cond="h1.idSalon = h2.idSalon",
                        joins="JOIN Salon s ON s.id = h1.idSalon", quien="s.nombre")
    return db.consultar(docente, (id_periodo,)) + db.consultar(salon, (id_periodo,))


def resumen_generados(id_periodo):
    """Cuántos bloques hay por carrera, nivel y paralelo en el período."""
    return db.consultar(
        "SELECT c.id AS idCarrera, c.nombre AS carrera, a.nivel, h.paralelo, COUNT(*) AS bloques "
        "FROM Horario h JOIN Asignatura a ON a.id = h.idAsignatura JOIN Carrera c ON c.id = a.idCarrera "
        "WHERE h.idPeriodo = ? GROUP BY c.id, c.nombre, a.nivel, h.paralelo ORDER BY c.nombre, a.nivel, h.paralelo",
        (id_periodo,))


# ==============================================================================
# Gestión: generar y descartar horarios (lo único que escribe este sistema)
# ==============================================================================
def _bloques_existentes(id_periodo):
    return [dict(dia=r["dia"], ini=r["ini"], fin=r["fin"], salon=r["idSalon"], docente=r["idDocente"],
                 grupo=(r["idCarrera"], r["nivel"], r["paralelo"]))
            for r in db.consultar(
                "SELECT h.dia, DATEPART(HOUR, h.horaInicio) * 60 + DATEPART(MINUTE, h.horaInicio) AS ini, "
                "DATEPART(HOUR, h.horaFin) * 60 + DATEPART(MINUTE, h.horaFin) AS fin, h.idSalon, h.idDocente, "
                "a.idCarrera, a.nivel, h.paralelo FROM Horario h JOIN Asignatura a ON a.id = h.idAsignatura "
                "WHERE h.idPeriodo = ?", (id_periodo,))]


def _choca(existentes, dia, ini, fin, salon, docente, grupo):
    for e in existentes:
        if e["dia"] != dia or not (e["ini"] < fin and ini < e["fin"]):
            continue
        if e["salon"] == salon or (docente and e["docente"] == docente) or e["grupo"] == grupo:
            return True
    return False


def generar(id_periodo, id_carrera, nivel, paralelos):
    """Crea bloques de 2 h sin cruces de salón, docente ni grupo. Devuelve (creados, avisos)."""
    carrera = db.uno("SELECT nombre FROM Carrera WHERE id = ?", (id_carrera,))
    if not carrera:
        raise ValueError("Selecciona una carrera válida.")
    if not paralelos:
        raise ValueError("Marca al menos un paralelo.")
    asignaturas = db.consultar(
        "SELECT a.id, a.nombre, a.horasSemanales, a.idDocente, CAST(d.estado AS INT) AS docente_activo "
        "FROM Asignatura a LEFT JOIN Docente d ON d.id = a.idDocente WHERE a.idCarrera = ? AND a.nivel = ? "
        "ORDER BY a.horasSemanales DESC, a.nombre", (id_carrera, nivel))
    if not asignaturas:
        raise ValueError("No hay asignaturas cargadas para esa carrera y nivel.")
    salones = db.consultar("SELECT id, capacidad FROM Salon WHERE estado = 'Disponible' ORDER BY capacidad, id")
    if not salones:
        raise ValueError("No hay salones disponibles.")

    existentes = _bloques_existentes(id_periodo)
    nuevos, avisos = [], []
    for par in paralelos:
        n_est = db.uno("SELECT COUNT(*) AS n FROM Estudiante WHERE carrera = ? AND nivel = ? "
                       "AND UPPER(RIGHT(RTRIM(curso), 1)) = ?", (carrera["nombre"], nivel, par))["n"]
        # primero los salones donde caben todos; si no hay, los demás
        orden = [s for s in salones if s["capacidad"] >= n_est] + [s for s in salones if s["capacidad"] < n_est]
        grupo = (id_carrera, nivel, par)
        for a in asignaturas:
            if db.uno("SELECT TOP 1 1 AS x FROM Horario WHERE idPeriodo = ? AND idAsignatura = ? AND paralelo = ?",
                      (id_periodo, a["id"], par)):
                avisos.append("%s · paralelo %s: ya tenía horario, no se tocó." % (a["nombre"], par))
                continue
            if not a["idDocente"] or not a["docente_activo"]:
                avisos.append("%s · paralelo %s: sin docente activo asignado." % (a["nombre"], par))
                continue
            usados = set()
            for _ in range(max(1, math.ceil((a["horasSemanales"] or 2) / 2))):
                puesto = False
                dias = [d for d in range(1, 6) if d not in usados] or list(range(1, 6))
                for dia in dias:
                    for hora in range(HORA_APERTURA, HORA_CIERRE - 1):
                        ini, fin = hora * 60, (hora + 2) * 60
                        for s in orden:
                            if not _choca(existentes, dia, ini, fin, s["id"], a["idDocente"], grupo):
                                existentes.append(dict(dia=dia, ini=ini, fin=fin, salon=s["id"],
                                                       docente=a["idDocente"], grupo=grupo))
                                nuevos.append((id_periodo, a["id"], a["idDocente"], s["id"], par, dia,
                                               "%02d:00" % hora, "%02d:00" % (hora + 2)))
                                usados.add(dia); puesto = True
                                break
                        if puesto: break
                    if puesto: break
                if not puesto:
                    avisos.append("%s · paralelo %s: no hay espacio libre para todos los bloques." % (a["nombre"], par))
    if nuevos:
        try:
            with db.transaccion() as cur:
                for fila in nuevos:
                    cur.execute("INSERT INTO Horario (idPeriodo, idAsignatura, idDocente, idSalon, paralelo, dia, "
                                "horaInicio, horaFin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", fila)
        except pyodbc.IntegrityError:
            raise ValueError("Ya existen bloques que chocan con los generados. Descarta el horario y vuelve a generarlo.")
    return len(nuevos), avisos


def descartar(id_periodo, id_carrera, nivel, paralelo=None):
    """Borra los bloques de una carrera y nivel (y paralelo, si se indica) del período."""
    sql = ("DELETE h FROM Horario h JOIN Asignatura a ON a.id = h.idAsignatura "
           "WHERE h.idPeriodo = ? AND a.idCarrera = ? AND a.nivel = ?")
    par = [id_periodo, id_carrera, nivel]
    if paralelo:
        sql += " AND h.paralelo = ?"; par.append(paralelo)
    with db.transaccion() as cur:
        cur.execute(sql, par)
        return cur.rowcount
