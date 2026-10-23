import pyodbc


SERVIDOR = r".\SQLEXPRESS"
BASE_DATOS = "BD_Gestion_Horario"

def obtener_conexion():
    cadena_conexion = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVIDOR};"
        f"DATABASE={BASE_DATOS};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(cadena_conexion)

def comprobar_conexion():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT DB_NAME()")
        print(f"Conexión correcta con la base de datos: {cursor.fetchone()[0]}")
    finally:
        conexion.close()

if __name__ == "__main__":
    comprobar_conexion()
