"""
Conexión a SQL Server (pyodbc) para el sistema de Gestión Académica.

Configuración por variables de entorno (opcionales):
  DB_DRIVER   (por defecto "ODBC Driver 17 for SQL Server")
  DB_SERVER   (por defecto "localhost\\SQLEXPRESS")#BD_Gestio_Horiorio #BD_Gestion_Horario
  DB_NAME     (por defecto "GestionAcademica")
  DB_USER / DB_PASSWORD   -> si no se definen, usa autenticación de Windows
  DB_ESTRICTO=1           -> si SQL Server falla, lanza el error en vez de usar SQLite

Si SQL Server no está disponible, se usa automáticamente un archivo SQLite local
(gestion_academica.db) para que la aplicación pueda probarse sin instalar nada.
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

DRIVER = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")
SERVER = os.environ.get("DB_SERVER", "localhost\\SQLEXPRESS")
BASE = os.environ.get("DB_NAME", "GestionAcademica")
USUARIO = os.environ.get("DB_USER")
CLAVE = os.environ.get("DB_PASSWORD")
RUTA_SQLITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gestion_academica.db")

MOTOR = None  # "sqlserver" o "sqlite" (se define en la primera conexión)


# ---------------------------------------------------------------- conexión
def _cadena(base: str) -> str:
    cad = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={base};TrustServerCertificate=yes;"
    if USUARIO:
        return cad + f"UID={USUARIO};PWD={CLAVE};"
    return cad + "Trusted_Connection=yes;"


def _crear_base_sqlserver(pyodbc) -> None:
    cx = pyodbc.connect(_cadena("master"), timeout=5, autocommit=True)
    cx.execute(f"IF DB_ID('{BASE}') IS NULL CREATE DATABASE [{BASE}]")
    cx.close()


def conectar():
    global MOTOR
    if MOTOR != "sqlite":
        try:
            import pyodbc
            if MOTOR is None:
                _crear_base_sqlserver(pyodbc)
            cx = pyodbc.connect(_cadena(BASE), timeout=5)
            MOTOR = "sqlserver"
            return cx
        except Exception as e:  # noqa: BLE001
            if os.environ.get("DB_ESTRICTO") == "1":
                raise
            print(f"[DB] No se pudo usar SQL Server ({e.__class__.__name__}). Usando SQLite local.")
            MOTOR = "sqlite"
    cx = sqlite3.connect(RUTA_SQLITE)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA foreign_keys = ON")
    return cx


def _filas(cur):
    columnas = [c[0] for c in cur.description]
    return [dict(zip(columnas, tuple(f))) for f in cur.fetchall()]


# ------------------------------------------------------------ operaciones
def consultar(sql: str, params: tuple = ()) -> list[dict]:
    cx = conectar()
    try:
        cur = cx.cursor()
        cur.execute(sql, params)
        return _filas(cur)
    finally:
        cx.close()


def ejecutar(sql: str, params: tuple = ()) -> int:
    """INSERT/UPDATE/DELETE. Devuelve filas afectadas."""
    cx = conectar()
    try:
        cur = cx.cursor()
        cur.execute(sql, params)
        cx.commit()
        return cur.rowcount
    finally:
        cx.close()


def insertar(sql: str, params: tuple = ()) -> int:
    """INSERT que devuelve el id generado."""
    cx = conectar()
    try:
        cur = cx.cursor()
        if MOTOR == "sqlserver":
            cur.execute("SET NOCOUNT ON; " + sql + "; SELECT CAST(SCOPE_IDENTITY() AS INT);", params)
            nuevo = cur.fetchone()[0]
        else:
            cur.execute(sql, params)
            nuevo = cur.lastrowid
        cx.commit()
        return nuevo
    finally:
        cx.close()


# ------------------------------------------------------------------ tablas
def _t(n: int) -> str:
    """Tipo texto según el motor (NVARCHAR en SQL Server, TEXT en SQLite)."""
    return f"NVARCHAR({n})" if MOTOR == "sqlserver" else "TEXT"


def _ddl():
    pk = "INT IDENTITY(1,1) PRIMARY KEY" if MOTOR == "sqlserver" else "INTEGER PRIMARY KEY AUTOINCREMENT"
    t = _t
    return {
        "usuarios": f"CREATE TABLE usuarios (id {pk}, usuario {t(50)} NOT NULL UNIQUE, "
                    f"clave_hash {t(300)} NOT NULL, rol {t(30)} NOT NULL)",
        "docentes": f"CREATE TABLE docentes (id {pk}, cedula {t(15)} NOT NULL UNIQUE, nombre {t(60)} NOT NULL, "
                    f"apellido {t(60)} NOT NULL, especialidad {t(80)} NULL, asignatura {t(100)} NULL, "
                    f"nivel INT NULL, estado INT NOT NULL DEFAULT 1)",
        "estudiantes": f"CREATE TABLE estudiantes (id {pk}, cedula {t(15)} NOT NULL UNIQUE, "
                       f"codigo_registro INT NOT NULL UNIQUE, nombre {t(60)} NOT NULL, apellido {t(60)} NOT NULL, "
                       f"correo_institucional {t(120)} NOT NULL UNIQUE, curso {t(5)} NOT NULL, "
                       f"carrera {t(80)} NOT NULL, nivel INT NOT NULL, asignatura {t(100)} NULL)",
        "salones": f"CREATE TABLE salones (id {pk}, numero INT NOT NULL UNIQUE, capacidad INT NOT NULL, "
                   f"tipo {t(20)} NOT NULL, estado {t(20)} NOT NULL DEFAULT 'Disponible')",
        "asignaturas": f"CREATE TABLE asignaturas (id {pk}, codigo INT NOT NULL UNIQUE, nombre {t(100)} NOT NULL, "
                       f"nivel INT NOT NULL, carrera {t(80)} NOT NULL, horas_semanales INT NOT NULL DEFAULT 4, "
                       f"docente_id INT NULL REFERENCES docentes(id))",
        "horarios": f"CREATE TABLE horarios (id {pk}, asignatura_id INT NOT NULL REFERENCES asignaturas(id), "
                    f"docente_id INT NULL REFERENCES docentes(id), salon_id INT NOT NULL REFERENCES salones(id), "
                    f"dia {t(15)} NOT NULL, hora_inicio INT NOT NULL, hora_fin INT NOT NULL, "
                    f"paralelo {t(5)} NOT NULL, periodo {t(15)} NOT NULL)",
    }


def _existe(tabla: str) -> bool:
    if MOTOR == "sqlserver":
        return bool(consultar("SELECT 1 AS x FROM sys.tables WHERE name = ?", (tabla,)))
    return bool(consultar("SELECT 1 AS x FROM sqlite_master WHERE type='table' AND name = ?", (tabla,)))


def _columnas(tabla: str) -> set:
    if MOTOR == "sqlserver":
        filas = consultar("SELECT COLUMN_NAME AS n FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", (tabla,))
    else:
        filas = consultar(f"PRAGMA table_info({tabla})")
        filas = [{"n": f["name"]} for f in filas]
    return {f["n"].lower() for f in filas}


def _migrar() -> None:
    """Agrega columnas nuevas a bases creadas con versiones anteriores del esquema."""
    palabra = "ADD" if MOTOR == "sqlserver" else "ADD COLUMN"
    if _existe("docentes"):
        cols = _columnas("docentes")
        if "asignatura" not in cols:
            ejecutar(f"ALTER TABLE docentes {palabra} asignatura {_t(100)} NULL")
        if "nivel" not in cols:
            ejecutar(f"ALTER TABLE docentes {palabra} nivel INT NULL")


def inicializar() -> None:
    """Crea tablas si no existen y carga datos de ejemplo."""
    conectar().close()  # fija MOTOR
    for tabla, sql in _ddl().items():
        if not _existe(tabla):
            ejecutar(sql)
    _migrar()

    if not consultar("SELECT 1 AS x FROM usuarios"):
        ejecutar("INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (?, ?, ?)",
                 ("admin", generate_password_hash("Admin2026"), "Administrador"))
    if not consultar("SELECT 1 AS x FROM salones"):
        for num, cap, tipo in [(101, 35, "Aula"), (102, 35, "Aula"), (205, 25, "Laboratorio"), (206, 25, "Laboratorio")]:
            ejecutar("INSERT INTO salones (numero, capacidad, tipo) VALUES (?, ?, ?)", (num, cap, tipo))
    if not consultar("SELECT 1 AS x FROM docentes"):
        d1 = insertar("INSERT INTO docentes (cedula, nombre, apellido, especialidad, asignatura, nivel) "
                      "VALUES (?, ?, ?, ?, ?, ?)", ("1310000001", "Juan", "Pérez", "Software", "Programación", 2))
        d2 = insertar("INSERT INTO docentes (cedula, nombre, apellido, especialidad, asignatura, nivel) "
                      "VALUES (?, ?, ?, ?, ?, ?)", ("1310000002", "María", "Gómez", "Bases de datos", "Base de Datos", 2))
        for cod, nom, niv, hrs, doc in [(2001, "Programación", 2, 4, d1), (2002, "Base de Datos", 2, 4, d2),
                                        (2003, "Estructuras de Datos", 2, 2, d1)]:
            ejecutar("INSERT INTO asignaturas (codigo, nombre, nivel, carrera, horas_semanales, docente_id) "
                     "VALUES (?, ?, ?, ?, ?, ?)", (cod, nom, niv, "Software", hrs, doc))
    if not consultar("SELECT 1 AS x FROM estudiantes"):
        for ced, cod, nom, ape, correo, curso, niv, asig in [
            ("1310000101", 5001, "Ana", "López", "ana.lopez@universidad.edu.ec", "A", 2, "Programación"),
            ("1310000102", 5002, "Carlos", "Ruiz", "carlos.ruiz@universidad.edu.ec", "B", 3, "Base de Datos")]:
            ejecutar("INSERT INTO estudiantes (cedula, codigo_registro, nombre, apellido, correo_institucional, "
                     "curso, carrera, nivel, asignatura) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (ced, cod, nom, ape, correo, curso, "Software", niv, asig))
