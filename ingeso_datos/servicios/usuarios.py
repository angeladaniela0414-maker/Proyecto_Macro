"""Autenticación y administración de usuarios (Usuario + tablas por rol)."""
import re

import pyodbc

from conexion_db import consultar, ejecutar, transaccion
from seguridad import clave_temporal, esta_cifrada, hash_clave, verificar_clave

CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _perfil_por_rol(uid):
    """Detecta el rol según la tabla donde existe el id."""
    est = consultar("SELECT nombre, apellido FROM Estudiante WHERE id = ?", (uid,))
    if est:
        return "estudiante", est[0]
    doc = consultar("SELECT nombre, apellido, estado FROM Docente WHERE id = ?", (uid,))
    if doc:
        return "docente", doc[0]
    ges = consultar("SELECT nombre, apellido FROM Gestion_Academica WHERE id = ?", (uid,))
    if ges:
        return "gestion", ges[0]
    return None, None


def _mejorar_hash(tabla, uid, guardada, clave):
    """Si la clave estaba en texto plano, se guarda cifrada tras un ingreso correcto."""
    if not esta_cifrada(guardada):
        ejecutar("UPDATE %s SET [contraseña] = ? WHERE id = ?" % tabla, (hash_clave(clave), uid))


DOMINIO = "live.uleam.edu.ec"


def autenticar(usuario, clave):
    """Devuelve los datos de sesión o None. ValueError si la cuenta no puede ingresar.

    `usuario` puede ser el correo completo, solo la parte anterior a la @ (se completa con
    el dominio institucional) o el usuario del administrador (ej. «admin»).
    """
    candidatos = [usuario] + ([usuario + "@" + DOMINIO] if "@" not in usuario else [])
    for correo in candidatos:
        fila = consultar(
            "SELECT id, [contraseña] AS clave FROM Usuario WHERE correoInstitucional = ?", (correo,))
        if fila:
            f = fila[0]
            if not verificar_clave(f["clave"], clave):
                return None
            rol, perfil = _perfil_por_rol(f["id"])
            if rol is None:
                raise ValueError("Tu usuario no tiene un rol asignado. Contacta a Gestión Académica.")
            if rol == "docente" and not perfil["estado"]:
                raise ValueError("Tu cuenta docente está inactiva. Contacta a Gestión Académica.")
            _mejorar_hash("Usuario", f["id"], f["clave"], clave)
            return {"rol": rol, "uid": f["id"], "correo": correo,
                    "nombre": perfil["nombre"], "apellido": perfil["apellido"]}

    adm = consultar(
        "SELECT id, [contraseña] AS clave FROM Administrador WHERE correoInstitucional = ?", (usuario,))
    if adm and verificar_clave(adm[0]["clave"], clave):
        _mejorar_hash("Administrador", adm[0]["id"], adm[0]["clave"], clave)
        return {"rol": "admin", "uid": adm[0]["id"], "correo": usuario,
                "nombre": "Administrador", "apellido": ""}
    return None


def asegurar_admin(usuario="admin", clave="1234"):
    """Crea el administrador inicial si no existe. Devuelve True si lo creó."""
    if consultar("SELECT 1 AS x FROM Administrador WHERE correoInstitucional = ?", (usuario,)):
        return False
    nuevo = consultar("SELECT ISNULL(MAX(id), 0) + 1 AS n FROM Administrador")[0]["n"]
    ejecutar("INSERT INTO Administrador (id, correoInstitucional, [contraseña]) VALUES (?, ?, ?)",
             (nuevo, usuario, hash_clave(clave)))
    return True


# --- Creación de usuarios -----------------------------------------------------
def _validar(correo, clave, nombre, apellido):
    if not CORREO_RE.match(correo or ""):
        raise ValueError("Ingresa un correo institucional válido.")
    if len(clave or "") < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not (nombre or "").strip() or not (apellido or "").strip():
        raise ValueError("Nombre y apellido son obligatorios.")


def _crear(correo, clave, insertar_rol):
    try:
        with transaccion() as cur:
            cur.execute("SELECT 1 FROM Usuario WHERE correoInstitucional = ?", (correo,))
            if cur.fetchone():
                raise ValueError("Ya existe un usuario con ese correo.")
            cur.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM Usuario WITH (UPDLOCK, HOLDLOCK)")
            nuevo = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (?, ?, ?)",
                (nuevo, correo, hash_clave(clave)))
            insertar_rol(cur, nuevo)
            return nuevo
    except pyodbc.IntegrityError:
        raise ValueError("Ya existe un registro con esos datos (correo o cédula repetidos).")


def crear_estudiante(correo, clave, nombre, apellido, carrera, nivel, curso,
                     cedula=None, codigo=None, asignatura=None):
    correo = (correo or "").strip().lower()
    _validar(correo, clave, nombre, apellido)
    if not carrera:
        raise ValueError("Selecciona la carrera.")
    try:
        nivel = int(nivel)
    except (TypeError, ValueError):
        raise ValueError("El nivel debe ser un número.")
    if not 1 <= nivel <= 12:
        raise ValueError("El nivel debe estar entre 1 y 12.")
    curso = (curso or "").strip().upper()[:30]
    if not curso:
        raise ValueError("Indica el paralelo (curso), por ejemplo A.")

    def rol(cur, uid):
        cur.execute(
            "INSERT INTO Estudiante (id, correoInstitucional, nombre, apellido, curso, carrera, nivel, "
            "cedula, codigoRegistro, asignatura) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, correo, nombre.strip(), apellido.strip(), curso, carrera, nivel,
             cedula, codigo, (asignatura or "").strip() or None))
    return _crear(correo, clave, rol)


def crear_docente(correo, clave, nombre, apellido, cedula, especialidad, nivel, asignatura=None):
    correo = (correo or "").strip().lower()
    _validar(correo, clave, nombre, apellido)
    cedula = (cedula or "").strip()
    if not re.fullmatch(r"\d{10}", cedula):
        raise ValueError("La cédula debe tener 10 dígitos.")
    try:
        nivel = int(nivel) if str(nivel or "").strip() else None
    except ValueError:
        raise ValueError("El nivel debe ser un número.")

    def rol(cur, uid):
        cur.execute(
            "INSERT INTO Docente (id, cedula, nombre, apellido, especialidad, nivel, estado, asignatura)"
            " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (uid, cedula, nombre.strip(), apellido.strip(), (especialidad or "").strip() or None, nivel,
             (asignatura or "").strip() or None))
    return _crear(correo, clave, rol)


# --- Contraseñas --------------------------------------------------------------
def restablecer_clave(correo):
    """Genera una clave temporal y la guarda cifrada. Devuelve la clave en claro."""
    temporal = clave_temporal()
    n = ejecutar("UPDATE Usuario SET [contraseña] = ? WHERE correoInstitucional = ?",
                 (hash_clave(temporal), correo))
    if not n:
        raise ValueError("No existe un usuario con ese correo.")
    return temporal


def correo_de(uid):
    f = consultar("SELECT correoInstitucional AS correo FROM Usuario WHERE id = ?", (uid,))
    return f[0]["correo"] if f else None


def cambiar_clave(rol, uid, actual, nueva):
    tabla = "Administrador" if rol == "admin" else "Usuario"
    f = consultar("SELECT [contraseña] AS clave FROM %s WHERE id = ?" % tabla, (uid,))
    if not f or not verificar_clave(f[0]["clave"], actual):
        raise ValueError("La contraseña actual no es correcta.")
    if len(nueva or "") < 8:
        raise ValueError("La nueva contraseña debe tener al menos 8 caracteres.")
    if nueva == actual:
        raise ValueError("La nueva contraseña debe ser distinta de la actual.")
    ejecutar("UPDATE %s SET [contraseña] = ? WHERE id = ?" % tabla, (hash_clave(nueva), uid))


def registrar_solicitud_clave(correo):
    """Registra la solicitud solo si el correo existe y no hay otra pendiente."""
    if not consultar("SELECT 1 AS x FROM Usuario WHERE correoInstitucional = ?", (correo,)):
        return
    if consultar("SELECT 1 AS x FROM SolicitudClave WHERE correo = ? AND estado = 'Pendiente'", (correo,)):
        return
    ejecutar("INSERT INTO SolicitudClave (correo) VALUES (?)", (correo,))
