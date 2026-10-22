"""Consultas y operaciones académicas: horarios, salones, tutorías, registro, gestión."""
from datetime import datetime, date

import pyodbc

from conexion_db import consultar, consultar_uno, ejecutar, insertar, transaccion
from seguridad import hash_clave

DIAS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes"}


def entero(v, defecto=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return defecto


def _hora(v, campo="hora"):
    try:
        return datetime.strptime((v or "").strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError("La %s no es válida (usa el formato HH:MM)." % campo)


def _minutos(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


# ==============================================================================
# Catálogos
# ==============================================================================
def periodo_activo():
    return consultar_uno("SELECT TOP 1 id, nombre FROM PeriodoAcademico WHERE activo = 1 ORDER BY id DESC")


def catalogos():
    return {
        "carreras": consultar("SELECT id, nombre FROM Carrera ORDER BY nombre"),
        "niveles": consultar("SELECT DISTINCT nivel FROM Asignatura ORDER BY nivel"),
        "paralelos": consultar("SELECT DISTINCT paralelo FROM Horario ORDER BY paralelo"),
        "asignaturas": consultar(
            "SELECT a.id, a.nombre, a.nivel FROM Asignatura a ORDER BY a.nivel, a.nombre"),
        "docentes": consultar(
            "SELECT id, nombre + ' ' + apellido AS nombre FROM Docente WHERE estado = 1 "
            "ORDER BY apellido, nombre"),
        "periodos": consultar("SELECT id, nombre, activo FROM PeriodoAcademico ORDER BY id DESC"),
    }


# ==============================================================================
# Horarios
# ==============================================================================
_SQL_HORARIO = """
SELECT h.id, h.dia,
       CONVERT(VARCHAR(5), h.horaInicio, 108) AS horaInicio,
       CONVERT(VARCHAR(5), h.horaFin, 108) AS horaFin,
       h.paralelo, a.nombre AS asignatura, a.codigo, a.nivel, c.nombre AS carrera,
       d.nombre + ' ' + d.apellido AS docente, s.nombre AS salon, p.nombre AS periodo
FROM Horario h
JOIN PeriodoAcademico p ON p.id = h.idPeriodo
JOIN Asignatura a ON a.id = h.idAsignatura
JOIN Carrera c ON c.id = a.idCarrera
LEFT JOIN Docente d ON d.id = h.idDocente
LEFT JOIN Salon s ON s.id = h.idSalon
"""


def horario(carrera=None, carrera_nombre=None, nivel=None, paralelo=None,
            asignatura=None, docente=None, periodo=None):
    cond, par = [], []
    if periodo:
        cond.append("h.idPeriodo = ?"); par.append(periodo)
    else:
        cond.append("p.activo = 1")
    if carrera:
        cond.append("c.id = ?"); par.append(carrera)
    if carrera_nombre:
        cond.append("c.nombre = ?"); par.append(carrera_nombre)
    if nivel:
        cond.append("a.nivel = ?"); par.append(nivel)
    if paralelo:
        cond.append("h.paralelo = ?"); par.append(paralelo)
    if asignatura:
        cond.append("a.id = ?"); par.append(asignatura)
    if docente:
        cond.append("h.idDocente = ?"); par.append(docente)
    sql = (_SQL_HORARIO + " WHERE " + " AND ".join(cond) +
           " ORDER BY h.horaInicio, h.dia, a.nivel, h.paralelo")
    return consultar(sql, par)


def _duracion(b):
    return (_minutos(b["horaFin"]) - _minutos(b["horaInicio"])) / 60.0


def horas_semanales(bloques):
    return sum(_duracion(b) for b in bloques)


def resumen_asignaturas(bloques):
    res = {}
    for b in bloques:
        k = (b["asignatura"], b["paralelo"], b["nivel"])
        r = res.setdefault(k, {"asignatura": b["asignatura"], "codigo": b["codigo"],
                               "paralelo": b["paralelo"], "nivel": b["nivel"],
                               "docente": b["docente"], "carrera": b["carrera"],
                               "horas": 0.0, "salones": set()})
        r["horas"] += _duracion(b)
        if b["salon"]:
            r["salones"].add(b["salon"])
    salida = sorted(res.values(), key=lambda r: (r["nivel"], r["asignatura"]))
    for r in salida:
        r["salones"] = ", ".join(sorted(r["salones"]))
    return salida


# ==============================================================================
# Estudiante
# ==============================================================================
def perfil_estudiante(uid):
    return consultar_uno(
        "SELECT e.id, e.nombre, e.apellido, e.correoInstitucional AS correo, e.carrera, e.nivel, e.curso, "
        "       c.id AS idCarrera, f.nombre AS facultad "
        "FROM Estudiante e LEFT JOIN Carrera c ON c.nombre = e.carrera "
        "LEFT JOIN Facultad f ON f.id = c.idFacultad WHERE e.id = ?", (uid,))


def _letra(curso):
    partes = (curso or "").strip().split()
    return partes[-1].upper()[:5] if partes else ""


def registro_activo(uid):
    return consultar_uno(
        "SELECT TOP 1 r.id, r.codigo, r.paralelo, r.nivel, r.fechaRegistro "
        "FROM Registro r JOIN PeriodoAcademico p ON p.id = r.idPeriodo "
        "WHERE r.idEstudiante = ? AND r.estado = 'Activo' AND p.activo = 1 ORDER BY r.id DESC", (uid,))


def paralelo_efectivo(perfil):
    reg = registro_activo(perfil["id"])
    return reg["paralelo"] if reg else _letra(perfil["curso"])


def horario_estudiante(perfil):
    return horario(carrera_nombre=perfil["carrera"], nivel=perfil["nivel"],
                   paralelo=paralelo_efectivo(perfil))


def paralelos_disponibles(carrera_nombre, nivel):
    f = consultar(
        "SELECT DISTINCT h.paralelo FROM Horario h "
        "JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
        "JOIN Asignatura a ON a.id = h.idAsignatura JOIN Carrera c ON c.id = a.idCarrera "
        "WHERE c.nombre = ? AND a.nivel = ? ORDER BY h.paralelo", (carrera_nombre, nivel))
    return [x["paralelo"] for x in f]


def registrar_horario(perfil, paralelo):
    periodo = periodo_activo()
    if not periodo:
        raise ValueError("No hay un período académico activo.")
    if paralelo not in paralelos_disponibles(perfil["carrera"], perfil["nivel"]):
        raise ValueError("Ese paralelo no está disponible para tu nivel.")
    with transaccion() as cur:
        cur.execute("UPDATE Registro SET estado = 'Anulado' "
                    "WHERE idEstudiante = ? AND idPeriodo = ? AND estado = 'Activo'",
                    (perfil["id"], periodo["id"]))
        cur.execute("INSERT INTO Registro (idEstudiante, idPeriodo, nivel, paralelo, estado) "
                    "OUTPUT INSERTED.id VALUES (?, ?, ?, ?, 'Activo')",
                    (perfil["id"], periodo["id"], perfil["nivel"], paralelo))
        rid = cur.fetchone()[0]
        codigo = "REG-%s-%05d" % (periodo["nombre"], rid)
        cur.execute("UPDATE Registro SET codigo = ? WHERE id = ?", (codigo, rid))
    return codigo


def registros_estudiante(uid):
    return consultar(
        "SELECT r.id, r.codigo, r.nivel, r.paralelo, r.fechaRegistro, r.estado, p.nombre AS periodo "
        "FROM Registro r JOIN PeriodoAcademico p ON p.id = r.idPeriodo "
        "WHERE r.idEstudiante = ? ORDER BY r.id DESC", (uid,))


def registro_detalle(uid, rid):
    return consultar_uno(
        "SELECT r.id, r.codigo, r.nivel, r.paralelo, r.fechaRegistro, r.estado, r.idPeriodo, "
        "       p.nombre AS periodo FROM Registro r JOIN PeriodoAcademico p ON p.id = r.idPeriodo "
        "WHERE r.id = ? AND r.idEstudiante = ?", (rid, uid))


# ==============================================================================
# Tutorías
# ==============================================================================
_SQL_TUTORIA = """
SELECT t.id, t.nombre, t.fecha, CONVERT(VARCHAR(5), t.horaInicio, 108) AS horaInicio,
       CONVERT(VARCHAR(5), t.horaFin, 108) AS horaFin, t.cupo, t.estado,
       d.nombre + ' ' + d.apellido AS docente, a.nombre AS asignatura, s.nombre AS salon,
       (SELECT COUNT(*) FROM TutoriaSolicitud x WHERE x.idTutoria = t.id AND x.estado = 'Solicitada') AS ocupados
       %s
FROM Tutoria t
JOIN Docente d ON d.id = t.idDocente
LEFT JOIN Asignatura a ON a.id = t.idAsignatura
LEFT JOIN Carrera c ON c.id = a.idCarrera
LEFT JOIN Salon s ON s.id = t.idSalon
"""


def tutorias_para_estudiante(perfil):
    sql = (_SQL_TUTORIA % ", (SELECT COUNT(*) FROM TutoriaSolicitud y WHERE y.idTutoria = t.id "
           "AND y.idEstudiante = ? AND y.estado = 'Solicitada') AS solicitada") + \
          (" WHERE t.estado = 'Programada' AND t.fecha >= CAST(GETDATE() AS DATE) "
           "AND (a.id IS NULL OR c.nombre = ?) ORDER BY t.fecha, t.horaInicio")
    return consultar(sql, (perfil["id"], perfil["carrera"]))


def tutorias_solicitadas(uid, solo_futuras=True):
    sql = (_SQL_TUTORIA % "") + (
        " JOIN TutoriaSolicitud q ON q.idTutoria = t.id AND q.idEstudiante = ? AND q.estado = 'Solicitada' "
        " WHERE t.estado = 'Programada' ")
    if solo_futuras:
        sql += "AND t.fecha >= CAST(GETDATE() AS DATE) "
    return consultar(sql + "ORDER BY t.fecha, t.horaInicio", (uid,))


def solicitar_tutoria(uid, id_tut):
    with transaccion() as cur:
        cur.execute("SELECT cupo FROM Tutoria WITH (UPDLOCK) WHERE id = ? AND estado = 'Programada' "
                    "AND fecha >= CAST(GETDATE() AS DATE)", (id_tut,))
        t = cur.fetchone()
        if not t:
            raise ValueError("La tutoría ya no está disponible.")
        cur.execute("SELECT COUNT(*) FROM TutoriaSolicitud WHERE idTutoria = ? AND estado = 'Solicitada'",
                    (id_tut,))
        if cur.fetchone()[0] >= t[0]:
            raise ValueError("La tutoría ya no tiene cupos.")
        cur.execute("SELECT id, estado FROM TutoriaSolicitud WHERE idTutoria = ? AND idEstudiante = ?",
                    (id_tut, uid))
        s = cur.fetchone()
        if s and s[1] == "Solicitada":
            raise ValueError("Ya solicitaste esta tutoría.")
        if s:
            cur.execute("UPDATE TutoriaSolicitud SET estado = 'Solicitada', fecha = GETDATE() WHERE id = ?", (s[0],))
        else:
            cur.execute("INSERT INTO TutoriaSolicitud (idTutoria, idEstudiante) VALUES (?, ?)", (id_tut, uid))


def cancelar_solicitud(uid, id_tut):
    ejecutar("UPDATE TutoriaSolicitud SET estado = 'Cancelada' "
             "WHERE idTutoria = ? AND idEstudiante = ? AND estado = 'Solicitada'", (id_tut, uid))


# ---- Docente ----
def tutorias_docente(uid):
    return consultar(_SQL_TUTORIA % "" + " WHERE t.idDocente = ? ORDER BY t.fecha DESC, t.horaInicio", (uid,))


def asignaturas_docente(uid):
    return consultar(
        "SELECT DISTINCT a.id, a.nombre, a.nivel FROM Horario h "
        "JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
        "JOIN Asignatura a ON a.id = h.idAsignatura WHERE h.idDocente = ? ORDER BY a.nivel, a.nombre", (uid,))


def _choca_horario(cur, campo, valor, dia, hi, hf):
    cur.execute("SELECT TOP 1 1 FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
                "WHERE h.%s = ? AND h.dia = ? AND h.horaInicio < CAST(? AS TIME) AND h.horaFin > CAST(? AS TIME)"
                % campo, (valor, dia, hf, hi))
    return cur.fetchone() is not None


def _choca_tutoria(cur, campo, valor, fecha, hi, hf):
    cur.execute("SELECT TOP 1 1 FROM Tutoria t WHERE t.%s = ? AND t.fecha = ? AND t.estado = 'Programada' "
                "AND t.horaInicio < CAST(? AS TIME) AND t.horaFin > CAST(? AS TIME)" % campo,
                (valor, fecha, hf, hi))
    return cur.fetchone() is not None


def crear_tutoria(uid, f):
    nombre = (f.get("nombre") or "").strip()
    if not 3 <= len(nombre) <= 120:
        raise ValueError("El nombre de la tutoría debe tener entre 3 y 120 caracteres.")
    try:
        fecha = datetime.strptime(f.get("fecha", ""), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("La fecha no es válida.")
    if fecha < date.today():
        raise ValueError("La fecha no puede estar en el pasado.")
    hi, hf = _hora(f.get("horaInicio"), "hora de inicio"), _hora(f.get("horaFin"), "hora de fin")
    if _minutos(hf) <= _minutos(hi):
        raise ValueError("La hora de fin debe ser posterior a la de inicio.")
    cupo = entero(f.get("cupo"), 0)
    if not 1 <= cupo <= 200:
        raise ValueError("El cupo debe estar entre 1 y 200.")
    id_asig = entero(f.get("asignatura"))
    if id_asig and id_asig not in [a["id"] for a in asignaturas_docente(uid)]:
        raise ValueError("Solo puedes crear tutorías de las asignaturas que dictas.")
    id_salon = entero(f.get("salon"))
    with transaccion() as cur:
        if id_salon:
            cur.execute("SELECT estado FROM Salon WHERE id = ?", (id_salon,))
            s = cur.fetchone()
            if not s or s[0] != "Disponible":
                raise ValueError("El salón seleccionado no está disponible.")
        dia = fecha.isoweekday()
        if dia <= 5 and _choca_horario(cur, "idDocente", uid, dia, hi, hf):
            raise ValueError("Tienes una clase en ese horario.")
        if _choca_tutoria(cur, "idDocente", uid, fecha, hi, hf):
            raise ValueError("Ya tienes otra tutoría en ese horario.")
        if id_salon:
            if dia <= 5 and _choca_horario(cur, "idSalon", id_salon, dia, hi, hf):
                raise ValueError("El salón está ocupado por una clase en ese horario.")
            if _choca_tutoria(cur, "idSalon", id_salon, fecha, hi, hf):
                raise ValueError("El salón ya está reservado para otra tutoría en ese horario.")
        cur.execute("INSERT INTO Tutoria (nombre, idDocente, idAsignatura, idSalon, fecha, horaInicio, horaFin, cupo) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (nombre, uid, id_asig, id_salon, fecha, hi, hf, cupo))


def cancelar_tutoria(uid, id_tut):
    with transaccion() as cur:
        cur.execute("UPDATE Tutoria SET estado = 'Cancelada' WHERE id = ? AND idDocente = ?", (id_tut, uid))
        if cur.rowcount:
            cur.execute("UPDATE TutoriaSolicitud SET estado = 'Cancelada' WHERE idTutoria = ? AND estado = 'Solicitada'",
                        (id_tut,))
        else:
            raise ValueError("No se encontró la tutoría.")


def solicitantes_tutoria(uid, id_tut):
    return consultar(
        "SELECT e.nombre, e.apellido, e.correoInstitucional AS correo, e.nivel, e.curso "
        "FROM TutoriaSolicitud q JOIN Tutoria t ON t.id = q.idTutoria "
        "JOIN Estudiante e ON e.id = q.idEstudiante "
        "WHERE q.idTutoria = ? AND t.idDocente = ? AND q.estado = 'Solicitada' ORDER BY e.apellido, e.nombre",
        (id_tut, uid))


def estudiantes_de_docente(uid, asignatura=None):
    sql = ("SELECT DISTINCT e.id, e.nombre, e.apellido, e.correoInstitucional AS correo, e.carrera, "
           "e.nivel, e.curso, a.nombre AS asignatura FROM Horario h "
           "JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
           "JOIN Asignatura a ON a.id = h.idAsignatura JOIN Carrera c ON c.id = a.idCarrera "
           "JOIN Estudiante e ON e.carrera = c.nombre AND e.nivel = a.nivel "
           "AND UPPER(RIGHT(RTRIM(e.curso), 1)) = h.paralelo WHERE h.idDocente = ? ")
    par = [uid]
    if asignatura:
        sql += "AND a.id = ? "; par.append(asignatura)
    return consultar(sql + "ORDER BY a.nombre, e.apellido, e.nombre", par)


# ==============================================================================
# Salones
# ==============================================================================
def salones(tipo=None, estado=None):
    ahora = datetime.now()
    cond, par = [], [ahora.isoweekday(), ahora.strftime("%H:%M"), ahora.strftime("%H:%M")]
    if tipo:
        cond.append("s.tipoSalon = ?"); par.append(tipo)
    if estado:
        cond.append("s.estado = ?"); par.append(estado)
    sql = ("SELECT s.id, s.numeroDeSalon, s.nombre, s.capacidad, s.tipoSalon, s.estado, "
           "CASE WHEN EXISTS (SELECT 1 FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
           "  WHERE h.idSalon = s.id AND h.dia = ? AND h.horaInicio <= CAST(? AS TIME) AND h.horaFin > CAST(? AS TIME)) "
           "THEN 1 ELSE 0 END AS ocupado FROM Salon s")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    return consultar(sql + " ORDER BY s.tipoSalon, s.nombre", par)


def salones_libres(dia, hi, hf):
    if dia not in DIAS:
        raise ValueError("Selecciona un día de lunes a viernes.")
    hi, hf = _hora(hi, "hora de inicio"), _hora(hf, "hora de fin")
    if _minutos(hf) <= _minutos(hi):
        raise ValueError("La hora de fin debe ser posterior a la de inicio.")
    return consultar(
        "SELECT s.id, s.nombre, s.capacidad, s.tipoSalon FROM Salon s WHERE s.estado = 'Disponible' "
        "AND NOT EXISTS (SELECT 1 FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
        "  WHERE h.idSalon = s.id AND h.dia = ? AND h.horaInicio < CAST(? AS TIME) AND h.horaFin > CAST(? AS TIME)) "
        "ORDER BY s.tipoSalon, s.nombre", (dia, hf, hi))


def crear_salon(numero, nombre, capacidad, tipo):
    nombre = (nombre or "").strip()
    numero, capacidad = entero(numero), entero(capacidad)
    if not nombre or numero is None or not capacidad or capacidad < 1:
        raise ValueError("Completa nombre, número y capacidad (mayor que 0).")
    if tipo not in ("Aula", "Laboratorio", "Auditorio"):
        raise ValueError("Tipo de salón no válido.")
    try:
        ejecutar("INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (?, ?, ?, ?)",
                 (numero, nombre, capacidad, tipo))
    except pyodbc.IntegrityError:
        raise ValueError("Ya existe un salón con ese nombre.")


def estado_salon(id_salon, estado):
    if estado not in ("Disponible", "Mantenimiento"):
        raise ValueError("Estado no válido.")
    ejecutar("UPDATE Salon SET estado = ? WHERE id = ?", (estado, id_salon))


def eliminar_salon(id_salon):
    if consultar("SELECT TOP 1 1 AS x FROM Horario WHERE idSalon = ?", (id_salon,)) or \
       consultar("SELECT TOP 1 1 AS x FROM Tutoria WHERE idSalon = ?", (id_salon,)):
        raise ValueError("El salón tiene clases o tutorías asignadas. Ponlo en mantenimiento en lugar de eliminarlo.")
    ejecutar("DELETE FROM Salon WHERE id = ?", (id_salon,))


# ==============================================================================
# Gestión académica
# ==============================================================================
def resumen_gestion():
    return consultar_uno(
        "SELECT (SELECT COUNT(*) FROM Docente WHERE estado = 1) AS docentes, "
        "       (SELECT COUNT(*) FROM Estudiante) AS estudiantes, "
        "       (SELECT COUNT(*) FROM Salon WHERE estado = 'Disponible') AS salones, "
        "       (SELECT COUNT(*) FROM Asignatura) AS asignaturas, "
        "       (SELECT COUNT(*) FROM SolicitudClave WHERE estado = 'Pendiente') AS solicitudes")


def perfil_gestion(uid):
    return consultar_uno("SELECT nombre, apellido, facultad, cargo FROM Gestion_Academica WHERE id = ?", (uid,))


def docentes():
    return consultar(
        "SELECT d.id, d.cedula, d.nombre, d.apellido, u.correoInstitucional AS correo, d.especialidad, "
        "d.nivel, d.estado, (SELECT COUNT(DISTINCT h.idAsignatura) FROM Horario h "
        "JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 WHERE h.idDocente = d.id) AS asignaturas "
        "FROM Docente d JOIN Usuario u ON u.id = d.id ORDER BY d.apellido, d.nombre")


def estado_docente(id_docente, activo):
    ejecutar("UPDATE Docente SET estado = ? WHERE id = ?", (1 if activo else 0, id_docente))


def estudiantes(carrera=None, nivel=None, curso=None):
    cond, par = [], []
    if carrera:
        cond.append("e.carrera = ?"); par.append(carrera)
    if nivel:
        cond.append("e.nivel = ?"); par.append(nivel)
    if curso:
        cond.append("UPPER(RIGHT(RTRIM(e.curso), 1)) = ?"); par.append(curso.upper())
    sql = ("SELECT TOP 500 e.id, e.nombre, e.apellido, e.correoInstitucional AS correo, e.carrera, e.nivel, e.curso "
           "FROM Estudiante e")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    return consultar(sql + " ORDER BY e.carrera, e.nivel, e.apellido, e.nombre", par)


def asignaturas(carrera=None, nivel=None):
    cond, par = [], []
    if carrera:
        cond.append("a.idCarrera = ?"); par.append(carrera)
    if nivel:
        cond.append("a.nivel = ?"); par.append(nivel)
    sql = ("SELECT a.id, a.codigo, a.nombre, a.nivel, a.horasSemanales, c.nombre AS carrera "
           "FROM Asignatura a JOIN Carrera c ON c.id = a.idCarrera")
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    return consultar(sql + " ORDER BY c.nombre, a.nivel, a.nombre", par)


def crear_asignatura(codigo, nombre, id_carrera, nivel, horas):
    codigo, nombre = (codigo or "").strip().upper(), (nombre or "").strip()
    id_carrera, nivel, horas = entero(id_carrera), entero(nivel), entero(horas, 4)
    if not codigo or not nombre or not id_carrera or not nivel or nivel < 1:
        raise ValueError("Completa código, nombre, carrera y nivel.")
    if not 1 <= horas <= 20:
        raise ValueError("Las horas semanales deben estar entre 1 y 20.")
    try:
        ejecutar("INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales) VALUES (?, ?, ?, ?, ?)",
                 (codigo, nombre, nivel, id_carrera, horas))
    except pyodbc.IntegrityError:
        raise ValueError("Ya existe una asignatura con ese código.")


def solicitudes_clave():
    return consultar("SELECT TOP 100 id, correo, fecha, estado FROM SolicitudClave ORDER BY "
                     "CASE estado WHEN 'Pendiente' THEN 0 ELSE 1 END, id DESC")


def marcar_solicitud(id_sol, estado):
    ejecutar("UPDATE SolicitudClave SET estado = ? WHERE id = ?", (estado, id_sol))


def solicitud(id_sol):
    return consultar_uno("SELECT id, correo, estado FROM SolicitudClave WHERE id = ?", (id_sol,))


# ---- Reportes (CSV) ----
REPORTES = {
    "docentes": ("Docentes",
                 "SELECT d.cedula AS Cedula, d.nombre AS Nombre, d.apellido AS Apellido, u.correoInstitucional AS Correo, "
                 "d.especialidad AS Especialidad, d.nivel AS Nivel, CASE d.estado WHEN 1 THEN 'Activo' ELSE 'Inactivo' END AS Estado "
                 "FROM Docente d JOIN Usuario u ON u.id = d.id ORDER BY d.apellido, d.nombre"),
    "estudiantes": ("Estudiantes",
                    "SELECT nombre AS Nombre, apellido AS Apellido, correoInstitucional AS Correo, carrera AS Carrera, "
                    "nivel AS Nivel, curso AS Paralelo FROM Estudiante ORDER BY carrera, nivel, apellido"),
    "salones": ("Salones",
                "SELECT numeroDeSalon AS Numero, nombre AS Nombre, tipoSalon AS Tipo, capacidad AS Capacidad, estado AS Estado "
                "FROM Salon ORDER BY tipoSalon, nombre"),
    "asignaturas": ("Asignaturas",
                    "SELECT a.codigo AS Codigo, a.nombre AS Asignatura, c.nombre AS Carrera, a.nivel AS Nivel, "
                    "a.horasSemanales AS Horas FROM Asignatura a JOIN Carrera c ON c.id = a.idCarrera "
                    "ORDER BY c.nombre, a.nivel, a.nombre"),
    "horarios": ("Horarios del periodo activo",
                 "SELECT c.nombre AS Carrera, a.nivel AS Nivel, h.paralelo AS Paralelo, a.nombre AS Asignatura, "
                 "CASE h.dia WHEN 1 THEN 'Lunes' WHEN 2 THEN 'Martes' WHEN 3 THEN 'Miercoles' WHEN 4 THEN 'Jueves' "
                 "ELSE 'Viernes' END AS Dia, CONVERT(VARCHAR(5), h.horaInicio, 108) AS Inicio, "
                 "CONVERT(VARCHAR(5), h.horaFin, 108) AS Fin, d.nombre + ' ' + d.apellido AS Docente, s.nombre AS Salon "
                 "FROM Horario h JOIN PeriodoAcademico p ON p.id = h.idPeriodo AND p.activo = 1 "
                 "JOIN Asignatura a ON a.id = h.idAsignatura JOIN Carrera c ON c.id = a.idCarrera "
                 "LEFT JOIN Docente d ON d.id = h.idDocente LEFT JOIN Salon s ON s.id = h.idSalon "
                 "ORDER BY c.nombre, a.nivel, h.paralelo, h.dia, h.horaInicio"),
}
