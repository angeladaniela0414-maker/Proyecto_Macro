"""Configuración del portal. Se puede cambiar aquí o con variables de entorno."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- SQL Server ---------------------------------------------------------------
# Instancia: "localhost", r"localhost\SQLEXPRESS", "MI-PC\\SQLEXPRESS", etc.
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "BD_Gestion_Horario")
# "ODBC Driver 17 for SQL Server" o "ODBC Driver 18 for SQL Server"
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
# Si DB_USUARIO queda vacío se usa autenticación de Windows (Trusted_Connection).
DB_USUARIO = os.getenv("DB_USUARIO", "")
DB_CLAVE = os.getenv("DB_CLAVE", "")

# --- Servidor web -------------------------------------------------------------
HOST = "0.0.0.0"              # escucha en todas las tarjetas de red
PUERTO = int(os.getenv("PUERTO", "80"))


def _clave_secreta():
    """Clave de sesión persistente (se crea una vez en secret.key)."""
    desde_entorno = os.getenv("SECRET_KEY")
    if desde_entorno:
        return desde_entorno
    ruta = BASE_DIR / "secret.key"
    if not ruta.exists():
        ruta.write_text(secrets.token_hex(32), encoding="utf-8")
    return ruta.read_text(encoding="utf-8").strip()


SECRET_KEY = _clave_secreta()
