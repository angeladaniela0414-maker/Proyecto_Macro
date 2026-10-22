"""Conexión a SQL Server (BD_Gestion_Horario)."""
from contextlib import contextmanager
import pyodbc

# ---- Ajusta estos datos a tu equipo ----
SERVIDOR = r"localhost\SQLEXPRESS"   # usa "localhost" si es la instancia predeterminada
BASE_DATOS = "BD_Gestion_Horario"
USUARIO = ""    # vacío = Autenticación de Windows. Si usas usuario de SQL Server, escríbelo aquí
CLAVE = ""


def _cadena():
    instalados = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not instalados:
        raise RuntimeError("No hay ningún driver ODBC para SQL Server. Instala 'ODBC Driver 18 for SQL Server'.")
    modernos = sorted(d for d in instalados if d.startswith("ODBC Driver"))
    driver = modernos[-1] if modernos else instalados[0]

    partes = [f"DRIVER={{{driver}}}", f"SERVER={SERVIDOR}", f"DATABASE={BASE_DATOS}"]
    if USUARIO:
        partes += [f"UID={USUARIO}", f"PWD={CLAVE}"]
    else:
        partes.append("Trusted_Connection=yes")
    if driver.startswith("ODBC Driver"):
        partes.append("TrustServerCertificate=yes")
    return ";".join(partes)


def consultar(sql, params=()):
    """SELECT: devuelve una lista de diccionarios."""
    con = pyodbc.connect(_cadena())
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        nombres = [c[0] for c in cur.description]
        return [dict(zip(nombres, fila)) for fila in cur.fetchall()]
    finally:
        con.close()


@contextmanager
def transaccion():
    """Entrega un cursor; hace commit al terminar o rollback si hay error."""
    con = pyodbc.connect(_cadena())
    try:
        yield con.cursor()
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
