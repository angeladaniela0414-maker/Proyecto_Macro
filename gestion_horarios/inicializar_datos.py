"""Crea las tablas académicas en BD_Gestion_Horario y (opcional) carga datos de demostración.

    python inicializar_datos.py              -> tablas + datos de demostración
    python inicializar_datos.py --sin-demo   -> solo tablas

No borra nada. Si un usuario demo ya existe, lo omite.
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import conexion_db as db
from servicios import academico as ac
from servicios import usuarios as us

CLAVE_DEMO = "Uleam2026*"
CARRERA = "Ingeniería en Software"


def ejecutar_script(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    lotes = [l.strip() for l in re.split(r"^\s*GO\s*$", texto, flags=re.I | re.M) if l.strip()]
    con = db.conectar(autocommit=True)
    cur = con.cursor()
    for lote in lotes:
        cur.execute(lote)
    con.close()


def _id(sql, params=()):
    f = db.consultar_uno(sql, params)
    return f["id"] if f else None


def sembrar_catalogo():
    if db.consultar_uno("SELECT COUNT(*) AS n FROM Facultad")["n"]:
        return
    fac = db.insertar("INSERT INTO Facultad (numeroDeFacultad, nombre) OUTPUT INSERTED.id VALUES (?, ?)",
                      (1, "Facultad de Ciencias Informáticas"))
    car = db.insertar("INSERT INTO Carrera (codigo, nombre, idFacultad) OUTPUT INSERTED.id VALUES (?, ?, ?)",
                      (101, CARRERA, fac))
    db.ejecutar("INSERT INTO PeriodoAcademico (nombre, fechaInicio, fechaFin, activo) VALUES (?, ?, ?, 1)",
                ("2026-1", date(2026, 4, 20), date(2026, 9, 4)))
    asignaturas = [
        ("SOF-401", "Programación Orientada a Objetos", 4), ("SOF-402", "Base de Datos Relacionales", 4),
        ("SOF-403", "Redes y Conectividad I", 4), ("SOF-404", "Sistemas Operativos", 4),
        ("SOF-405", "Ingeniería de Software II", 4), ("SOF-201", "Fundamentos de Programación", 2),
        ("SOF-202", "Matemática Discreta", 2), ("SOF-601", "Arquitectura de Software", 6),
        ("SOF-602", "Administración de Servidores", 6),
    ]
    for cod, nom, niv in asignaturas:
        db.ejecutar("INSERT INTO Asignatura (codigo, nombre, nivel, idCarrera, horasSemanales) VALUES (?,?,?,?,4)",
                    (cod, nom, niv, car))
    salones = [(102, "Aula 102", 40, "Aula"), (201, "Aula 201", 40, "Aula"), (204, "Aula 204", 35, "Aula"),
               (205, "Aula 205", 35, "Aula"), (301, "Aula 301", 40, "Aula"), (1, "Lab 1 - FCI", 30, "Laboratorio"),
               (2, "Lab 2 - FCI", 30, "Laboratorio"), (3, "Lab 3 - FCI", 30, "Laboratorio"),
               (4, "Lab Redes", 25, "Laboratorio")]
    for num, nom, cap, tipo in salones:
        db.ejecutar("INSERT INTO Salon (numeroDeSalon, nombre, capacidad, tipoSalon) VALUES (?,?,?,?)",
                    (num, nom, cap, tipo))


def _crear(fn, *args):
    try:
        return fn(*args)
    except ValueError as e:
        print("   - omitido (%s)" % e)
        return None


def sembrar_usuarios():
    ids = {}
    docentes = [("perez", "jperez", "Juan", "Pérez", "1300000001", "Programación"),
                ("mora", "mmora", "María", "Mora", "1300000002", "Bases de datos"),
                ("santos", "csantos", "Carlos", "Santos", "1300000003", "Sistemas y servidores"),
                ("rivas", "arivas", "Ana", "Rivas", "1300000004", "Redes"),
                ("garcia", "pgarcia", "Pedro", "García", "1300000005", "Matemática")]
    for clave, usr, nom, ape, ced, esp in docentes:
        correo = "%s@live.uleam.edu.ec" % usr
        ids[clave] = _crear(us.crear_docente, correo, CLAVE_DEMO, nom, ape, ced, esp, None) or \
            _id("SELECT id FROM Usuario WHERE correoInstitucional = ?", (correo,))
    if not db.consultar("SELECT 1 AS x FROM Usuario WHERE correoInstitucional = 'gestion@live.uleam.edu.ec'"):
        with db.transaccion() as cur:
            cur.execute("SELECT ISNULL(MAX(id),0)+1 FROM Usuario")
            n = cur.fetchone()[0]
            from seguridad import hash_clave
            cur.execute("INSERT INTO Usuario (id, correoInstitucional, [contraseña]) VALUES (?,?,?)",
                        (n, "gestion@live.uleam.edu.ec", hash_clave(CLAVE_DEMO)))
            cur.execute("INSERT INTO Gestion_Academica (id, nombre, apellido, facultad, carrera, cargo) "
                        "VALUES (?,?,?,?,?,?)", (n, "Laura", "Vera", "Facultad de Ciencias Informáticas",
                                                  CARRERA, "Coordinadora académica"))
    est = [("dcarvajal", "Daniela", "Carvajal", 4, "A"), ("mzambrano", "Mateo", "Zambrano", 4, "B"),
           ("lintriago", "Lucía", "Intriago", 2, "A")]
    for usr, nom, ape, niv, cur_ in est:
        ids[usr] = _crear(us.crear_estudiante, "%s@live.uleam.edu.ec" % usr, CLAVE_DEMO, nom, ape,
                          CARRERA, niv, cur_) or \
            _id("SELECT id FROM Usuario WHERE correoInstitucional = ?", ("%s@live.uleam.edu.ec" % usr,))
    return ids


def sembrar_horarios(ids):
    if db.consultar_uno("SELECT COUNT(*) AS n FROM Horario")["n"]:
        return
    per = ac.periodo_activo()["id"]
    A = lambda c: _id("SELECT id FROM Asignatura WHERE codigo = ?", (c,))
    S = lambda n: _id("SELECT id FROM Salon WHERE nombre = ?", (n,))
    M, T = ("08:00", "10:00"), ("10:00", "12:00")
    # (asignatura, paralelo, docente, salón, [(día, franja), ...])
    plan = [
        ("SOF-401", "A", "perez", "Lab 1 - FCI", [(1, M), (3, M)]),
        ("SOF-402", "A", "mora", "Lab 3 - FCI", [(2, M), (5, T)]),
        ("SOF-403", "A", "rivas", "Lab Redes", [(1, T), (3, T)]),
        ("SOF-404", "A", "santos", "Aula 204", [(5, M), (4, M)]),
        ("SOF-405", "A", "perez", "Aula 205", [(2, T), (4, T)]),
        ("SOF-401", "B", "perez", "Lab 2 - FCI", [(1, T), (3, T)]),
        ("SOF-402", "B", "mora", "Lab 3 - FCI", [(2, T), (5, M)]),
        ("SOF-403", "B", "rivas", "Lab Redes", [(1, M), (3, M)]),
        ("SOF-404", "B", "santos", "Aula 204", [(4, T), (5, T)]),
        ("SOF-405", "B", "perez", "Aula 205", [(2, M), (4, M)]),
        ("SOF-201", "A", "garcia", "Aula 102", [(1, M), (3, M)]),
        ("SOF-202", "A", "garcia", "Aula 102", [(2, M), (4, M)]),
        ("SOF-601", "A", "santos", "Aula 301", [(1, M), (3, M)]),
        ("SOF-602", "A", "santos", "Lab Redes", [(2, T), (3, T)]),
    ]
    for cod, par, doc, salon, bloques in plan:
        for dia, (hi, hf) in bloques:
            db.ejecutar("INSERT INTO Horario (idPeriodo, idAsignatura, idDocente, idSalon, paralelo, dia, horaInicio, horaFin) "
                        "VALUES (?,?,?,?,?,?,?,?)", (per, A(cod), ids[doc], S(salon), par, dia, hi, hf))
    hoy = date.today()
    tut = [("Tutoría de Refactorización", "perez", "SOF-401", "Lab 2 - FCI", hoy + timedelta(days=1), "14:00", "15:00", 15),
           ("Refuerzo de consultas SQL", "mora", "SOF-402", "Lab 3 - FCI", hoy + timedelta(days=3), "15:00", "16:00", 12)]
    ids_t = []
    for nom, doc, cod, salon, fecha, hi, hf, cupo in tut:
        ids_t.append(db.insertar(
            "INSERT INTO Tutoria (nombre, idDocente, idAsignatura, idSalon, fecha, horaInicio, horaFin, cupo) "
            "OUTPUT INSERTED.id VALUES (?,?,?,?,?,?,?,?)", (nom, ids[doc], A(cod), S(salon), fecha, hi, hf, cupo)))
    if ids.get("dcarvajal"):
        perfil = ac.perfil_estudiante(ids["dcarvajal"])
        ac.registrar_horario(perfil, "A")
        ac.solicitar_tutoria(ids["dcarvajal"], ids_t[0])
        ac.solicitar_tutoria(ids["dcarvajal"], ids_t[1])


def main():
    carpeta = Path(__file__).parent / "sql"
    print("Creando tablas...")
    ejecutar_script(carpeta / "03_Horarios.sql")
    if "--sin-demo" in sys.argv:
        print("Listo (sin datos de demostración).")
        return
    print("Cargando datos de demostración...")
    sembrar_catalogo()
    ids = sembrar_usuarios()
    sembrar_horarios(ids)
    print("\nListo. Usuarios de prueba (clave: %s):" % CLAVE_DEMO)
    print("  Estudiante .....: dcarvajal@live.uleam.edu.ec  (también mzambrano@, lintriago@)")
    print("  Docente ........: jperez@live.uleam.edu.ec     (también mmora@, csantos@, arivas@, pgarcia@)")
    print("  Gestión académ. : gestion@live.uleam.edu.ec")


if __name__ == "__main__":
    main()
