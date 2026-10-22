"""Configuración. Se cambia aquí o con variables de entorno."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- SQL Server 2022 (base que ya existe: BD_Gestion_Horario) ------------------
DB_SERVER = os.getenv("DB_SERVER", "localhost")      # ej.: r"localhost\SQLEXPRESS"
DB_NAME = os.getenv("DB_NAME", "BD_Gestion_Horario")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")   # o "ODBC Driver 17 for SQL Server"
DB_USUARIO = os.getenv("DB_USUARIO", "")             # vacío = autenticación de Windows
DB_CLAVE = os.getenv("DB_CLAVE", "")

# --- Servidor web -------------------------------------------------------------
HOST = "0.0.0.0"                                     # escucha en todas las tarjetas de red
PUERTO = int(os.getenv("PUERTO", "80"))

# --- Sesión -------------------------------------------------------------------
HORAS_SESION = 12                                    # sin «Recordarme»
DIAS_RECORDAR = 7                                    # con «Recordarme»


def _clave_secreta():
    desde_entorno = os.getenv("SECRET_KEY")
    if desde_entorno:
        return desde_entorno
    ruta = BASE_DIR / "secret.key"
    if not ruta.exists():
        ruta.write_text(secrets.token_hex(32), encoding="utf-8")
    return ruta.read_text(encoding="utf-8").strip()


SECRET_KEY = _clave_secreta()
