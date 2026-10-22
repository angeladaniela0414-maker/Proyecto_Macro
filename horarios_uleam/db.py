"""Conexión a SQL Server (solo lectura, salvo la generación de horarios)."""
import datetime
import decimal
from contextlib import contextmanager

import pyodbc

import config


def _cadena():
    partes = ["DRIVER={%s}" % config.DB_DRIVER, "SERVER=%s" % config.DB_SERVER,
              "DATABASE=%s" % config.DB_NAME, "TrustServerCertificate=yes"]
    if config.DB_USUARIO:
        partes += ["UID=%s" % config.DB_USUARIO, "PWD=%s" % config.DB_CLAVE]
    else:
        partes.append("Trusted_Connection=yes")
    return ";".join(partes)


def _valor(v):
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, datetime.date):
        return v.isoformat()
    if isinstance(v, datetime.time):
        return v.strftime("%H:%M")
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def filas(cur):
    columnas = [c[0] for c in cur.description]
    return [{c: _valor(v) for c, v in zip(columnas, f)} for f in cur.fetchall()]


@contextmanager
def transaccion():
    """Cursor con confirmación al salir (o reversa si hay error)."""
    con = pyodbc.connect(_cadena(), timeout=5)
    cur = con.cursor()
    try:
        yield cur
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def consultar(sql, params=()):
    with transaccion() as cur:
        cur.execute(sql, params)
        return filas(cur)


def uno(sql, params=()):
    r = consultar(sql, params)
    return r[0] if r else None
